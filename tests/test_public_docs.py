import importlib.util

import httpx
import pytest

from src import config
from src.config import ROOT_DIR, Settings, get_settings


@pytest.mark.asyncio
async def test_production_docs_use_public_prefix_and_preserve_auth(monkeypatch):
    settings = Settings(
        _env_file=None,
        app_env="production",
        app_root_path="/max/app",
        max_bot_token="unit-test-token-not-a-real-secret",
    )
    monkeypatch.setattr(config, "get_settings", lambda: settings)
    # Load a separate app so production route registration cannot affect other tests.
    spec = importlib.util.spec_from_file_location("production_docs_app", ROOT_DIR / "src/app.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    app = module.app
    app.dependency_overrides[get_settings] = lambda: settings
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="https://example.com/max/app/"
    ) as client:
        docs = await client.get("docs")
        assert docs.status_code == 200
        assert "url: '/max/app/openapi.json'" in docs.text
        response = await client.get("openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert schema["openapi"].startswith("3.1.")
        assert {"url": "/max/app"} in schema["servers"]
        assert schema["components"]["securitySchemes"]["MaxInitData"]["name"] == "X-Max-Init-Data"
        assert {"MaxInitData": []} in schema["paths"]["/api/v1/profile"]["get"]["security"]
        assert not any("/examples/" in path for path in schema["paths"])
        assert "/api/v1/geocode" not in schema["paths"]
        for path in ("api/v1/auth/me", "api/v1/profile"):
            assert (await client.get(path)).status_code == 401
        for path in ("redoc", "api/v1/examples/trip-request", "api/v1/geocode"):
            assert (await client.get(path)).status_code == 404
