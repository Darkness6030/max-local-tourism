from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest

from src.api.routes import get_container
from src.app import app
from src.config import Settings, get_settings
from src.errors import ServiceError
from src.models import GeoPoint, TripRequest
from src.services.geocoding import _is_matching_city
from src.services.planner import validate_city_distance
from tests.test_auth import TOKEN, signed_data


def city(lat=55.75, lon=37.61):
    return GeoPoint(
        query="Москва", title="Москва", address="Россия", latitude=lat, longitude=lon
    )


def test_city_matching_rejects_regions_villages_and_partial_names():
    raw = {
        "name": "Тверь",
        "addresstype": "city",
        "address": {"country_code": "ru", "city": "Тверь"},
    }
    assert _is_matching_city(SimpleNamespace(raw=raw), "г. Тверь, Тверская область")
    assert not _is_matching_city(SimpleNamespace(raw=raw), "Твер")
    for kind in ("state", "village", "county", "hamlet"):
        assert not _is_matching_city(
            SimpleNamespace(raw={**raw, "addresstype": kind}), "Тверь"
        )
    assert not _is_matching_city(
        SimpleNamespace(raw={**raw, "address": {"country_code": "by"}}), "Тверь"
    )


def test_distance_uses_unrounded_boundary(monkeypatch):
    from src.services import planner

    for distance in (5, 599.49, 599.99):
        monkeypatch.setattr(
            planner, "distance_km", lambda a, b, distance=distance: distance
        )
        assert validate_city_distance(city(), city()) == distance
    for distance in (0, 4.9, 600, 600.01):
        monkeypatch.setattr(
            planner, "distance_km", lambda a, b, distance=distance: distance
        )
        with pytest.raises(ServiceError):
            validate_city_distance(city(), city())


@pytest.mark.asyncio
async def test_validation_and_generation_cannot_bypass_radius():
    geocoder = SimpleNamespace(
        geocode=AsyncMock(
            side_effect=lambda name: (
                city() if name == "Москва" else city(43.115, 131.885)
            )
        )
    )
    jobs = SimpleNamespace(submit=AsyncMock())
    app.dependency_overrides[get_container] = lambda: SimpleNamespace(
        geocoding=geocoder, jobs=jobs
    )
    app.dependency_overrides[get_settings] = lambda: Settings(
        _env_file=None, max_bot_token=TOKEN
    )
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://localhost"
        ) as c:
            url = "/api/v1/cities/validate?origin=Москва&destination=Владивосток"
            assert (await c.get(url)).status_code == 401
            headers = {"X-Max-Init-Data": signed_data(user_id=42)}
            assert (await c.get(url, headers=headers)).status_code == 422
            response = await c.post(
                "/api/v1/trips/jobs",
                headers=headers,
                json=TripRequest(destination="Владивосток").model_dump(mode="json"),
            )
            assert response.status_code == 422
            jobs.submit.assert_not_awaited()
            geocoder.geocode.side_effect = lambda name: (
                city() if name == "Москва" else city(56.859, 35.895)
            )
            response = await c.get(url.replace("Владивосток", "Тверь"), headers=headers)
            assert response.status_code == 200
            assert 0 < response.json()["distance_km"] < 1000
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.parametrize("manual", [True, False])
async def test_planner_checks_radius_before_external_planning(manual):
    from src.models import DestinationSuggestion
    from src.services.planner import TripPlanner

    geocoder = SimpleNamespace(
        geocode=AsyncMock(
            side_effect=lambda name: (
                city() if name == "Москва" else city(43.115, 131.885)
            )
        )
    )
    weather = SimpleNamespace(forecast=AsyncMock())
    ai = SimpleNamespace(
        suggest_destination=AsyncMock(
            return_value=DestinationSuggestion(
                name="Владивосток", region="Приморский край", reason="Проверка ограничения расстояния"
            )
        )
    )
    planner = TripPlanner(
        geocoding=geocoder, weather=weather, schedule=SimpleNamespace(), gigachat=ai
    )
    with pytest.raises(ServiceError):
        await planner.generate(
            TripRequest(destination="Владивосток" if manual else None)
        )
    weather.forecast.assert_not_awaited()
