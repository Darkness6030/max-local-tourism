import json
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest
from pydantic import ValidationError

from src import cities
from src.api.routes import get_container
from src.app import app
from src.cities import CityCatalog, get_city_catalog, load_city_catalog
from src.config import Settings, get_settings
from src.models import (
    ProfilePreferences,
    ProfilePreferencesUpdate,
    TripJobCreated,
    TripParameters,
    TripRequest,
    UserProfile,
)
from src.sample import sample_trip
from src.services.gigachat_ai import GigaChatService
from tests.test_auth import TOKEN, signed_data
from tests.test_cities import city
from tests.test_destinations import candidates


@pytest.fixture
def custom_catalog(tmp_path, monkeypatch):
    """Only a temporary config changes: no production cities or source edits."""
    payload = load_city_catalog().model_dump(mode="json")
    payload["cities"][0]["enabled"] = False
    payload["cities"].append({
        "id": "test-city", "name": "Тестоград",
        "geocode_query": "Тестоград, Тестовая область",
    })
    payload["default_origin"] = "test-city"
    path = tmp_path / "cities.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    catalog = load_city_catalog(path)
    monkeypatch.setattr(cities, "load_city_catalog", lambda: catalog)
    get_city_catalog.cache_clear()
    try:
        yield catalog
    finally:
        get_city_catalog.cache_clear()


def test_config_alone_controls_defaults_and_validation(custom_catalog):
    assert TripRequest().origin == "Тестоград"
    assert ProfilePreferences().origin == "Тестоград"
    assert ProfilePreferencesUpdate(origin="Тестоград").origin == "Тестоград"
    for name in ("Москва", "Неизвестный город"):
        for model in (TripRequest, ProfilePreferencesUpdate):
            with pytest.raises(ValidationError, match="Город отправления недоступен"):
                model(origin=name)
    # Historical snapshots are independent of the current catalog.
    assert TripParameters(origin="Москва").origin == "Москва"
    assert TripParameters(origin="Удалённый город").origin == "Удалённый город"
    assert sample_trip().request.origin == "Москва"


@pytest.mark.parametrize("change", [
    {"cities": []},
    {"default_origin": "missing"},
    {"cities": [{"id": "one", "name": "Город", "enabled": False}], "default_origin": "one"},
    {"cities": [{"id": "one", "name": "Город"}, {"id": "one", "name": "Другой"}], "default_origin": "one"},
    {"cities": [{"id": "one", "name": "Город"}, {"id": "two", "name": "город"}], "default_origin": "one"},
    {"cities": [{"id": "one", "name": "Город", "enabeld": True}], "default_origin": "one"},
    {"cities": [{"id": "one", "name": "Город", "hero_image": "../secret"}], "default_origin": "one"},
    {"cities": [{"id": "one", "name": "Город", "destination_hints": ["Тула", "тула"]}], "default_origin": "one"},
])
def test_invalid_catalog_fails_early(change):
    payload = load_city_catalog().model_dump(mode="json")
    with pytest.raises(ValidationError):
        CityCatalog.model_validate({**payload, **change})


@pytest.mark.asyncio
async def test_public_config_and_all_write_endpoints_use_catalog(custom_catalog):
    geocoder = SimpleNamespace(geocode=AsyncMock(side_effect=lambda name: (
        city() if name == "Тестоград, Тестовая область" else city(56.859, 35.895)
    )))
    store = SimpleNamespace(update_profile=AsyncMock(return_value=UserProfile(onboarding_completed=True)))
    created = TripJobCreated(id=uuid4(), status_url="/api/v1/trips/jobs/test")
    jobs = SimpleNamespace(submit=AsyncMock(return_value=created))
    app.dependency_overrides[get_container] = lambda: SimpleNamespace(geocoding=geocoder, store=store, jobs=jobs)
    app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None, max_bot_token=TOKEN)
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://localhost") as client:
            config = (await client.get("/api/v1/app-config")).json()
            health = (await client.get("/api/v1/health")).json()
            assert config["origins"] == health["integrations"]["supported_origins"] == ["Санкт-Петербург", "Тестоград"]
            assert config["default_origin"] == "Тестоград"
            details = config["origin_details"][-1]
            assert details["from_label"] == "из города «Тестоград»"
            assert details["hero_image"] == "journey.webp"
            assert details["ticket_note"] is None
            assert "geocode_query" not in details and "destination_hints" not in details
            headers = {"X-Max-Init-Data": signed_data(user_id=42)}
            for origin, expected in [("Тестоград", 200), ("Москва", 422), ("Неизвестный город", 422)]:
                response = await client.get("/api/v1/cities/validate", headers=headers,
                                            params={"origin": origin, "destination": "Тверь"})
                assert response.status_code == expected
                response = await client.put("/api/v1/profile", headers=headers, json={"origin": origin})
                assert response.status_code == expected
                if expected == 422:
                    for endpoint in ("/trips/jobs", "/trips/generate", "/destinations/suggest"):
                        response = await client.post("/api/v1" + endpoint, headers=headers, json={"origin": origin})
                        assert response.status_code == 422
            jobs.submit.assert_not_awaited()
            response = await client.post("/api/v1/trips/jobs", headers=headers, json={"origin": "Тестоград"})
            assert response.status_code == 202
            assert jobs.submit.call_args.args[0].origin == "Тестоград"
            store.update_profile.assert_awaited_once()
            geocoder.geocode.assert_any_await("Тестоград, Тестовая область")
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_new_city_generates_without_editorial_hints(custom_catalog):
    service = GigaChatService(credentials=None, scope="", model="", verify_ssl_certs=True, ca_bundle_file=None, timeout=10)
    service._structured = AsyncMock(return_value=candidates(("Тверь", 95)))
    result = await service.suggest_destination(TripRequest())
    assert result.name == "Тверь"
    prompt = service._structured.call_args.kwargs["prompt"]
    assert "Тестоград" in prompt
    assert "Таруса" not in prompt and "Гатчина" not in prompt


@pytest.mark.asyncio
@pytest.mark.parametrize("destination", [None, "Коломна"])
async def test_planner_uses_configured_geocode_query(custom_catalog, destination):
    from src.services.planner import TripPlanner
    from tests.test_planner import FailingSchedule, FakeAI, FakeGeocoding, FakeWeather

    fixture_geocoder = FakeGeocoding()

    async def geocode(query):
        return await fixture_geocoder.geocode("Москва" if query == "Тестоград, Тестовая область" else query)

    geocoder = SimpleNamespace(geocode=AsyncMock(side_effect=geocode))
    ai = FakeAI()
    ai.suggest_destination = AsyncMock(return_value=candidates(("Коломна", 95)).candidates[0])
    planner = TripPlanner(geocoding=geocoder, weather=FakeWeather(), schedule=FailingSchedule(), gigachat=ai)
    result = await planner.generate(TripRequest(destination=destination))
    assert result.request.origin == "Тестоград"
    geocoder.geocode.assert_any_await("Тестоград, Тестовая область")


@pytest.mark.asyncio
async def test_disabled_city_profile_and_old_trips_remain_readable(custom_catalog, store):
    plan = sample_trip()
    await store.put(plan, "max:42")
    await store.update_profile("max:42", ProfilePreferences(origin="Москва", interests=["Природа"]))
    restored = await store.get_profile("max:42")
    assert restored.preferences.origin == "Тестоград"
    assert restored.preferences.interests == ["Природа"]
    assert (await store.get(plan.id, "max:42")).request.origin == "Москва"


def test_shipped_catalog_has_available_covers():
    from src.config import ROOT_DIR

    catalog = load_city_catalog()
    for item in catalog.cities:
        assert (ROOT_DIR / "frontend/src/assets" / item.hero_image).is_file()
