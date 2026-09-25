from datetime import date

import httpx
import pytest

from src.models import GeoPoint
from src.services.weather import WeatherService


@pytest.mark.asyncio
async def test_open_meteo_is_normalized() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["timezone"] == "auto"
        return httpx.Response(
            200,
            json={
                "timezone": "Europe/Moscow",
                "daily": {
                    "time": ["2026-08-22"],
                    "weather_code": [61],
                    "temperature_2m_min": [11.24],
                    "temperature_2m_max": [20.86],
                    "precipitation_probability_max": [72],
                    "precipitation_sum": [3.42],
                    "wind_speed_10m_max": [4.18],
                },
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        service = WeatherService(client, provider="open-meteo")
        result = await service.forecast(
            GeoPoint(
                query="Коломна",
                title="Коломна",
                address="Коломна, Россия",
                latitude=55.09,
                longitude=38.76,
            ),
            date(2026, 8, 22),
            1,
        )

    assert result.provider == "Open-Meteo"
    assert result.days[0].description == "слабый дождь"
    assert result.days[0].temperature_max_c == 20.9
    assert result.days[0].precipitation_probability_percent == 72
