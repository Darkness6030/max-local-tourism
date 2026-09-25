import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest
from fastapi import FastAPI

from src.api.routes import get_container, router
from src.auth import current_identity
from src.errors import ServiceError
from src.sample import sample_trip
from src.store import TripStore


@pytest.mark.asyncio
async def test_packing_persists_and_scopes_to_owner(store):
    plan = sample_trip()
    await store.put(plan, "max:42")
    assert await store.set_packed(plan.id, "max:43", 0, True) is None
    assert await store.set_packed(uuid4(), "max:42", 0, True) is None
    await asyncio.gather(
        store.set_packed(plan.id, "max:42", 0, True),
        store.set_packed(plan.id, "max:42", 1, True),
    )
    await store.sessions.kw["bind"].dispose()
    restored = TripStore(store.sessions)
    assert (await restored.get(plan.id, "max:42")).packed_items == [0, 1]
    await restored.set_packed(plan.id, "max:42", 0, True)
    assert (await restored.set_packed(plan.id, "max:42", 1, False)).packed_items == [0]
    with pytest.raises(ServiceError):
        await restored.set_packed(plan.id, "max:42", len(plan.packing_list), True)
    assert (await restored.get(plan.id, "max:42")).packed_items == [0]


@pytest.mark.asyncio
async def test_only_trip_changes_reset_packing(store):
    plan = sample_trip()
    await store.put(plan, "max:42")
    await store.set_packed(plan.id, "max:42", 0, True)
    # Saving the unchanged plan, even with an outdated checklist, preserves checks.
    await store.put(plan, "max:42")
    assert (await store.get(plan.id, "max:42")).packed_items == [0]
    for field, value in (
        ("title", "Новый заголовок"),
        ("notes", ["Изменённая заметка"]),
        ("packing_list", list(reversed(plan.packing_list))),
        ("request", plan.request.model_copy(update={"travelers": 3})),
    ):
        plan = await store.set_packed(plan.id, "max:42", 0, True)
        setattr(plan, field, value)
        await store.put(plan, "max:42")
        assert (await store.get(plan.id, "max:42")).packed_items == []
    plan.packed_items = [0]
    plan.id = uuid4()
    await store.put(plan, "max:42")
    assert (await store.get(plan.id, "max:42")).packed_items == []


@pytest.mark.asyncio
async def test_packing_endpoint_validation_and_owner():
    plan = sample_trip()
    store = SimpleNamespace(set_packed=AsyncMock(return_value=plan))
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_container] = lambda: SimpleNamespace(store=store)
    app.dependency_overrides[current_identity] = lambda: SimpleNamespace(owner_id="max:42")
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        url = f"/api/v1/trips/{plan.id}/packing"
        for payload in ({"item_index": -1, "checked": True},
                        {"item_index": 0, "checked": "yes"}):
            assert (await client.patch(url, json=payload)).status_code == 422
        store.set_packed.assert_not_awaited()
        response = await client.patch(url, json={"item_index": 0, "checked": True})
        assert response.status_code == 200
        store.set_packed.assert_awaited_once_with(plan.id, "max:42", 0, True)
        store.set_packed.return_value = None
        assert (await client.patch(url, json={"item_index": 0, "checked": True})).status_code == 404


def test_old_trip_without_checklist_remains_readable():
    from src.models import TripPlan
    payload = sample_trip().model_dump(mode="json")
    payload.pop("packed_items")
    assert TripPlan.model_validate(payload).packed_items == []
