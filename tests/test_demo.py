import httpx
import pytest

from src.app import app


@pytest.mark.asyncio
async def test_demo_form_is_available() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/demo")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert 'id="trip-form"' in response.text
    assert "/api/v1/trips/jobs" in response.text
    assert '<option value="Москва"' in response.text
    assert '<option value="Санкт-Петербург"' in response.text
    assert 'name="preferences"' in response.text
