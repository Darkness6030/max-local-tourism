import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest
from aiohttp import web
from fastapi import FastAPI
from sqlalchemy import select

from src.api.routes import get_container, router
from src.auth import current_identity
from src.config import get_settings
from src.database import TransportReminderRecord
from src.errors import ServiceError
from src.models import SettlementRef, TransportOption, TransportOptions
from src.sample import sample_trip
from src.services.reminders import ReminderStore, send_reminder
from tests.test_bot_welcome import settings
from tests.test_max_sdk import mock_max_api, sent_message

NOW = datetime(2030, 1, 1, 8, tzinfo=timezone.utc)


async def seed(store):
    plan = sample_trip()
    outbound = [TransportOption(
        departure=NOW + timedelta(hours=1, minutes=i * 5),
        arrival=NOW + timedelta(hours=2, minutes=i * 5), duration_minutes=60,
        from_station="Москва", to_station="Коломна", transport_type="bus", route_number="42",
        buy_url="https://rasp.yandex.ru/",
    ) for i in range(2)]
    plan.transport = TransportOptions(
        origin=SettlementRef(code="c213", title="Москва"),
        destination=SettlementRef(code="c10734", title="Коломна"),
        outbound=outbound,
        return_trip=[outbound[0].model_copy(update={"departure": NOW + timedelta(hours=8),
                     "from_station": "Коломна", "to_station": "Москва"})],
    )
    await store.put(plan, "max:42")
    return plan, ReminderStore(store.sessions)


@pytest.mark.asyncio
async def test_choices_are_exclusive_independent_durable_and_owner_scoped(store):
    plan, reminders = await seed(store)
    assert await reminders.get(plan.id, "max:43") is None
    assert await reminders.set(plan.id, "max:43", "outbound", 0, now=NOW) is None
    assert await reminders.set(uuid4(), "max:42", "outbound", 0, now=NOW) is None
    await reminders.set(plan.id, "max:42", "outbound", 0, now=NOW)
    await reminders.set(plan.id, "max:42", "return_trip", 0, now=NOW)
    await asyncio.gather(*(reminders.set(plan.id, "max:42", "outbound", i, now=NOW) for i in (0, 1)))
    await store.sessions.kw["bind"].dispose()
    restored = ReminderStore(store.sessions)
    state = await restored.get(plan.id, "max:42")
    assert state.outbound in (0, 1) and state.return_trip == 0
    async with store.sessions() as session:
        rows = (await session.scalars(select(TransportReminderRecord))).all()
        assert len(rows) == 6
        assert len({row.option_index for row in rows if row.direction == "outbound"}) == 1
    state = await restored.set(plan.id, "max:42", "outbound", None, now=NOW)
    assert state.outbound is None and state.return_trip == 0
    with pytest.raises(ServiceError):
        await restored.set(plan.id, "max:42", "outbound", 9, now=NOW)
    with pytest.raises(ServiceError):
        await restored.set(plan.id, "max:42", "outbound", 0, now=NOW + timedelta(hours=2))


@pytest.mark.asyncio
async def test_three_deadlines_no_early_or_duplicate_sends_and_idempotent_selection(store):
    plan, reminders = await seed(store)
    await reminders.set(plan.id, "max:42", "outbound", 0, now=NOW)
    send = AsyncMock()
    assert not await reminders.deliver_one(send, now=NOW)
    for minutes in (30, 10, 0):
        due = NOW + timedelta(hours=1, minutes=-minutes)
        assert await reminders.deliver_one(send, now=due)
        assert send.call_args.args[0].minutes_before == minutes
        assert send.call_args.args[0].owner_id == "max:42"
        assert not await reminders.deliver_one(send, now=due)
        await reminders.set(plan.id, "max:42", "outbound", 0, now=due)
        assert not await reminders.deliver_one(send, now=due)
    assert send.await_count == 3


@pytest.mark.asyncio
async def test_replacement_disable_delete_and_plan_edit_cancel_future_sends(store):
    plan, reminders = await seed(store)
    await reminders.set(plan.id, "max:42", "outbound", 0, now=NOW)
    await reminders.set(plan.id, "max:42", "outbound", 1, now=NOW)
    send = AsyncMock()
    assert not await reminders.deliver_one(send, now=NOW + timedelta(minutes=30))
    await reminders.set(plan.id, "max:42", "outbound", None, now=NOW)
    assert not await reminders.deliver_one(send, now=NOW + timedelta(minutes=35))
    await reminders.set(plan.id, "max:42", "outbound", 0, now=NOW)
    plan.title = "Изменённая поездка"
    await store.put(plan, "max:42")
    assert (await reminders.get(plan.id, "max:42")).outbound is None
    await reminders.set(plan.id, "max:42", "outbound", 0, now=NOW)
    await store.delete(plan.id, "max:42")
    assert not await reminders.deliver_one(send, now=NOW + timedelta(minutes=30))
    send.assert_not_awaited()


@pytest.mark.asyncio
async def test_late_activation_and_restart_skip_stale_notifications(store):
    plan, reminders = await seed(store)
    await reminders.set(plan.id, "max:42", "outbound", 0, now=NOW + timedelta(minutes=45))
    send = AsyncMock()
    assert not await reminders.deliver_one(send, now=NOW + timedelta(minutes=45))
    # Server was down at the 10-minute deadline: do not send a stale backlog.
    assert await reminders.deliver_one(send, now=NOW + timedelta(minutes=59))
    send.assert_not_awaited()
    assert await reminders.deliver_one(send, now=NOW + timedelta(hours=1))
    assert send.call_args.args[0].minutes_before == 0


@pytest.mark.asyncio
async def test_delivery_retry_and_parallel_workers_do_not_duplicate_success(store):
    plan, reminders = await seed(store)
    await reminders.set(plan.id, "max:42", "outbound", 0, now=NOW)
    due = NOW + timedelta(minutes=30)
    send = AsyncMock(side_effect=RuntimeError("Network unavailable"))
    assert await reminders.deliver_one(send, now=due)
    assert not await reminders.deliver_one(send, now=due + timedelta(seconds=10))
    send.side_effect = None
    results = await asyncio.gather(*(reminders.deliver_one(send, now=due + timedelta(seconds=15)) for _ in range(2)))
    assert sorted(results) == [False, True]
    assert send.await_count == 2


@pytest.mark.asyncio
async def test_shared_trip_does_not_copy_reminders(store):
    plan, reminders = await seed(store)
    await reminders.set(plan.id, "max:42", "outbound", 0, now=NOW)
    token = await store.publish_share(plan.id, "max:42")
    copy = await store.import_share(token, "max:43")
    assert (await reminders.get(copy.id, "max:43")).outbound is None


@pytest.mark.asyncio
async def test_api_validates_choice_identity_and_availability():
    from src.services.reminders import ReminderSelection

    selected = ReminderSelection(outbound=0)
    reminders = SimpleNamespace(get=AsyncMock(return_value=selected), set=AsyncMock(return_value=selected))
    identity = SimpleNamespace(mode="max", owner_id="max:42")
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_container] = lambda: SimpleNamespace(reminders=reminders)
    app.dependency_overrides[current_identity] = lambda: identity
    app.dependency_overrides[get_settings] = settings
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        url = f"/api/v1/trips/{uuid4()}/reminders"
        assert (await client.get(url)).json() == {"outbound": 0, "return_trip": None, "available": True}
        for value in (-1, True, "1"):
            assert (await client.put(url + "/outbound", json={"option_index": value})).status_code == 422
        assert (await client.put(url + "/wrong", json={"option_index": 0})).status_code == 422
        assert (await client.put(url + "/outbound", json={"option_index": 0, "user_id": 43})).status_code == 422
        assert (await client.put(url + "/outbound", json={"option_index": 0})).status_code == 200
        assert reminders.set.call_args.args[1:] == ("max:42", "outbound", 0)
        reminders.set.return_value = None
        assert (await client.put(url + "/outbound", json={"option_index": 0})).status_code == 404
        identity.mode = "local"
        assert (await client.put(url + "/outbound", json={"option_index": 0})).status_code == 403


@pytest.mark.asyncio
async def test_sdk_sends_private_max_notification_with_notify_true(store, monkeypatch):
    plan, reminders = await seed(store)
    await reminders.set(plan.id, "max:42", "outbound", 0, now=NOW)
    async with mock_max_api(monkeypatch, lambda request: web.json_response(sent_message())) as api:
        await reminders.deliver_one(lambda row: send_reminder(settings(), row), now=NOW + timedelta(minutes=30))
    request = api.requests[0]
    assert request["path"] == "/messages" and request["query"] == {"user_id": "42"}
    assert request["body"]["notify"] is True
    assert "через 30 минут" in request["body"]["text"]
    assert "Москва → Коломна" in request["body"]["text"]
    assert "Автобус №42" in request["body"]["text"]


@pytest.mark.asyncio
async def test_disable_waits_for_inflight_send_then_cancels_remaining_events(store):
    plan, reminders = await seed(store)
    await reminders.set(plan.id, "max:42", "outbound", 0, now=NOW)
    sending, finish = asyncio.Event(), asyncio.Event()

    async def send(row):
        sending.set()
        await finish.wait()

    delivery = asyncio.create_task(reminders.deliver_one(send, now=NOW + timedelta(minutes=30)))
    await asyncio.wait_for(sending.wait(), timeout=2)
    disabling = asyncio.create_task(reminders.set(plan.id, "max:42", "outbound", None, now=NOW))
    with pytest.raises(TimeoutError):
        await asyncio.wait_for(asyncio.shield(disabling), timeout=0.05)
    finish.set()
    await delivery
    assert (await disabling).outbound is None
    assert not await reminders.deliver_one(AsyncMock(), now=NOW + timedelta(minutes=50))


@pytest.mark.asyncio
async def test_background_worker_starts_and_stops_with_persisted_due_reminder(store, monkeypatch):
    from src.services import reminders as module

    plan, reminders = await seed(store)
    now = datetime.now(timezone.utc)
    plan.transport.outbound[0].departure = now + timedelta(minutes=30) - timedelta(seconds=1)
    await store.put(plan, "max:42")
    await reminders.set(plan.id, "max:42", "outbound", 0, now=now - timedelta(seconds=2))
    delivered = asyncio.Event()

    async def send(settings, row):
        assert row.minutes_before == 30 and row.owner_id == "max:42"
        delivered.set()

    monkeypatch.setattr(module, "send_reminder", send)
    worker = module.ReminderWorker(reminders, settings())
    worker.start()
    try:
        await asyncio.wait_for(delivered.wait(), timeout=2)
        # Wait for the send transaction to commit before exercising graceful close.
        for _ in range(100):
            async with store.sessions() as session:
                row = await session.get(TransportReminderRecord, (plan.id, "outbound", 30))
                if row.sent_at:
                    break
            await asyncio.sleep(0.01)
        assert row.sent_at is not None
    finally:
        await worker.close()
    assert worker.task.done()
