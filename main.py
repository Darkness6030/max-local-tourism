"""Точка входа MVP. Весь код приложения находится в ``src``."""

from src import app as application

app = application.app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True, proxy_headers=False)
