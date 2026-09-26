import asyncio
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest

from src.api.routes import get_container
from src.app import app
from src.config import Settings, get_settings
from src.sample import sample_trip
from tests.test_auth import TOKEN, signed_data


@pytest.mark.asyncio
async def test_share_import_is_private_idempotent_and_independent(store):
    plan = sample_trip()
    await store.put(plan, "max:42")
    assert await store.publish_share(plan.id, "max:43") is None
    await store.set_packed(plan.id, "max:42", 0, True)
    token = await store.publish_share(plan.id, "max:42")
    assert token == await store.publish_share(plan.id, "max:42")
    assert await store.import_share(uuid4(), "max:43") is None
    assert (await store.import_share(token, "max:42")).id == plan.id
    copies = await asyncio.gather(*(store.import_share(token, "max:43") for _ in range(5)))
    copied = copies[0]
    assert all(copy.id == copied.id for copy in copies)
    assert copied.id != plan.id
    assert copied.packed_items == []
    assert copied.itinerary == plan.itinerary
    assert (await store.list("max:43")).total == 1
    assert await store.get(plan.id, "max:43") is None
    assert await store.get(copied.id, "max:42") is None
    assert await store.publish_share(copied.id, "max:43") == token
    await store.delete(copied.id, "max:43")
    replacement = await store.import_share(token, "max:43")
    assert replacement.id != copied.id
    await store.delete(plan.id, "max:42")
    assert await store.import_share(token, "max:44") is None
    assert await store.get(replacement.id, "max:43") is not None


@pytest.mark.asyncio
async def test_share_api_requires_auth_and_owner(store):
    plan = sample_trip()
    await store.put(plan, "max:42")
    app.dependency_overrides[get_container] = lambda: SimpleNamespace(store=store)
    app.dependency_overrides[get_settings] = lambda: Settings(
        _env_file=None, max_bot_token=TOKEN, max_bot_username="test_bot",
    )
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://localhost",
        ) as client:
            path = f"/api/v1/trips/{plan.id}/share"
            owner = {"X-Max-Init-Data": signed_data(user_id=42)}
            recipient = {"X-Max-Init-Data": signed_data(user_id=43)}
            assert (await client.post(path)).status_code == 401
            assert (await client.post(path, headers=recipient)).status_code == 404
            published = await client.post(path, headers=owner)
            assert published.status_code == 200
            result = published.json()
            assert result["text"].endswith(result["url"])
            token = result["url"].split("trip_")[-1]
            path = f"/api/v1/shared-trips/{token}/import"
            assert (await client.post(path)).status_code == 401
            imported = await client.post(path, headers=recipient)
            assert imported.status_code == 200
            assert (await client.post(path, headers=recipient)).json()["id"] == imported.json()["id"]
    finally:
        app.dependency_overrides.clear()
