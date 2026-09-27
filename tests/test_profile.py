import asyncio
from types import SimpleNamespace

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.routes import get_container
from src.app import app
from src.config import Settings, get_settings
from src.database import UserProfileRecord
from src.models import ProfilePreferences
from src.store import TripStore
from tests.test_auth import TOKEN, signed_data


@pytest.mark.asyncio
async def test_onboarding_persists_across_connections_and_is_idempotent(store):
    assert not (await store.get_profile("max:42")).onboarding_completed
    await asyncio.gather(*(store.complete_onboarding("max:42") for _ in range(3)))
    async with store.sessions() as session:
        timestamp = (await session.get(UserProfileRecord, "max:42")).onboarding_completed_at
    await store.complete_onboarding("max:42")
    async with store.sessions() as session:
        assert (await session.get(UserProfileRecord, "max:42")).onboarding_completed_at == timestamp

    old_engine = store.sessions.kw["bind"]
    async with old_engine.connect() as connection:
        schema = await connection.scalar(text("SELECT current_schema()"))
    await old_engine.dispose()
    engine = create_async_engine(old_engine.url, connect_args={"server_settings": {"search_path": schema}})
    try:
        restored = TripStore(async_sessionmaker(engine, expire_on_commit=False))
        assert (await restored.get_profile("max:42")).onboarding_completed
        assert not (await restored.get_profile("max:43")).onboarding_completed
        assert not (await restored.get_profile("local:42")).onboarding_completed
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_profile_api_uses_verified_owner(store):
    app.dependency_overrides[get_container] = lambda: SimpleNamespace(store=store)
    app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None, max_bot_token=TOKEN)
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://localhost"
        ) as client:
            for method, path in [("GET", "/profile"), ("PUT", "/profile/onboarding")]:
                response = await client.request(method, "/api/v1" + path)
                assert response.status_code == 401
                response = await client.request(
                    method, "/api/v1" + path, headers={"X-Max-Init-Data": "invalid"}
                )
                assert response.status_code == 401
            owner = {"X-Max-Init-Data": signed_data(user_id=42)}
            stranger = {"X-Max-Init-Data": signed_data(user_id=43)}
            assert (await client.get("/api/v1/profile", headers=owner)).json() == {
                "onboarding_completed": False, "preferences": ProfilePreferences().model_dump(mode="json")
            }
            for _ in range(2):
                response = await client.put(
                    "/api/v1/profile/onboarding", headers=owner, json={"owner_id": "max:43"}
                )
                assert response.status_code == 200
                assert response.json()["onboarding_completed"]
            assert (await client.get("/api/v1/profile", headers=owner)).json()["onboarding_completed"]
            assert not (await client.get("/api/v1/profile", headers=stranger)).json()["onboarding_completed"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_profile_preferences_persist_without_completing_onboarding(store):
    preferences = ProfilePreferences(display_name="  Анна  ", avatar_style="mountain", avatar_color="sage",
                                     origin="Санкт-Петербург", pace="relaxed", interests=["Природа", "Природа"])
    saved = await store.update_profile("max:42", preferences)
    assert saved.preferences.display_name == "Анна"
    assert saved.preferences.interests == ["Природа"]
    assert not saved.onboarding_completed
    restored = TripStore(store.sessions)
    assert (await restored.get_profile("max:42")) == saved
    assert (await restored.get_profile("max:43")).preferences == ProfilePreferences()
    assert (await restored.get_profile("local:42")).preferences == ProfilePreferences()
    completed = await store.complete_onboarding("max:42")
    assert completed.onboarding_completed
    assert completed.preferences == saved.preferences
    updated = await store.update_profile("max:42", ProfilePreferences(display_name="Ирина"))
    assert updated.onboarding_completed
    assert updated.preferences.display_name == "Ирина"


@pytest.mark.asyncio
async def test_profile_update_api_validation_and_ownership(store):
    app.dependency_overrides[get_container] = lambda: SimpleNamespace(store=store)
    app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None, max_bot_token=TOKEN)
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://localhost") as client:
            owner = {"X-Max-Init-Data": signed_data(user_id=42)}
            payload = ProfilePreferences(display_name="Анна", avatar_style="sun").model_dump(mode="json")
            assert (await client.put("/api/v1/profile", json=payload)).status_code == 401
            assert (await client.put("/api/v1/profile", json=payload, headers={"X-Max-Init-Data": "invalid"})).status_code == 401
            response = await client.put("/api/v1/profile", json=payload, headers=owner)
            assert response.status_code == 200
            assert response.json()["preferences"] == payload
            for bad in [{"owner_id": "max:43"}, {"display_name": "x" * 61}, {"avatar_style": "unknown"},
                        {"origin": "Париж"}, {"pace": "fast"}, {"interests": ["unknown"]}, {"display_name": "A\x00B"}]:
                assert (await client.put("/api/v1/profile", json={**payload, **bad}, headers=owner)).status_code == 422
            assert (await client.get("/api/v1/profile", headers=owner)).json()["preferences"] == payload
            stranger = {"X-Max-Init-Data": signed_data(user_id=43)}
            assert (await client.get("/api/v1/profile", headers=stranger)).json()["preferences"] == ProfilePreferences().model_dump(mode="json")
    finally:
        app.dependency_overrides.clear()
