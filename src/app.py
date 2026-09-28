from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.api.bot import router as bot_router
from src.api.miniapp import router as miniapp_router
from src.api.routes import development_router, router
from src.cities import get_city_catalog
from src.config import ROOT_DIR, get_settings
from src.container import Container
from src.errors import ServiceError

settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.app_log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
# Provider URLs may contain API keys; do not log httpx request URLs at INFO.
logging.getLogger("httpx").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_city_catalog()  # Fail before starting services when the catalog is invalid.
    container = Container.build(settings)
    app.state.container = container
    try:
        await container.start()
        yield
    finally:
        await container.close()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Backend-MVP персонального ИИ-планировщика поездок выходного дня: "
        "ИИ, Яндекс Расписания, geopy/Nominatim и погодные API."
    ),
    lifespan=lifespan,
    root_path=settings.app_root_path,
    docs_url=None if settings.app_env == "production" else "/docs",
    redoc_url=None if settings.app_env == "production" else "/redoc",
    openapi_url=None if settings.app_env == "production" else "/openapi.json",
)

app.include_router(router)
app.include_router(bot_router)
app.include_router(miniapp_router)
if settings.app_env != "production":
    app.include_router(development_router)

app.mount("/static", StaticFiles(directory=ROOT_DIR / "src" / "static"), name="static")


@app.middleware("http")
async def response_security(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    path = request.url.path.removeprefix(request.scope.get("root_path", ""))
    if path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/", include_in_schema=False)
async def root() -> FileResponse:
    return FileResponse(
        ROOT_DIR / "src" / "static" / "index.html",
        headers={"Cache-Control": "no-cache"},
    )


@app.exception_handler(ServiceError)
async def service_error_handler(_: Request, exc: ServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "service": exc.service,
            "details": None,
        },
    )
