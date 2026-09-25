from datetime import timedelta
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.errors import ServiceError
from src.models import JobState, TripJobStatus
from src.sample import sample_trip
from src.store import TripStore


@pytest.mark.asyncio
async def test_restart_preserves_completed_trip_and_recovers_interrupted_job(store):
    plan = sample_trip()
    # Past plans must stay readable after request validation's date horizon.
    plan.request.start_date -= timedelta(days=100)
    done = TripJobStatus(id=uuid4(), events=[],  status=JobState.RUNNING, progress=70, message="Работаем")
    interrupted = TripJobStatus(id=uuid4(), events=[],  status=JobState.QUEUED, progress=0, message="Ожидание")
    await store.create_job(done, "max:42", 3)
    await store.finish_job(done.id, "max:42", plan)
    await store.create_job(interrupted, "max:43", 3)
    old_engine = store.sessions.kw["bind"]
    # Completely new connection pool, same isolated schema, no process cache.
    async with old_engine.connect() as connection:
        from sqlalchemy import text
        schema = await connection.scalar(text("SELECT current_schema()"))
    url = old_engine.url
    await old_engine.dispose()
    engine = create_async_engine(url, connect_args={"server_settings": {"search_path": schema}})
    try:
        restored = TripStore(async_sessionmaker(engine, expire_on_commit=False))
        await restored.recover_interrupted_jobs()
        result = await restored.get(plan.id, "max:42")
        assert result.model_dump(mode="json") == plan.model_dump(mode="json")
        job = await restored.get_job(done.id, "max:42")
        assert job.status == JobState.SUCCEEDED and job.progress == 100
        assert job.result.id == plan.id
        assert (await restored.get_job(interrupted.id, "max:43")).status == JobState.FAILED
        assert (await restored.list("max:42")).items[0].id == plan.id
        assert (await restored.list("max:43")).items == []
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_history_pagination_with_equal_timestamps_and_owner_isolation(store):
    plan = sample_trip()
    ids = set()
    for _ in range(5):
        item = plan.model_copy(update={"id": uuid4()})
        ids.add(item.id)
        await store.put(item, "max:42")
    foreign = plan.model_copy(update={"id": uuid4()})
    await store.put(foreign, "max:43")
    found = []
    cursor = None
    while True:
        page = await store.list("max:42", limit=2, cursor=cursor)
        assert page.total == 5
        found.extend(item.id for item in page.items)
        cursor = page.next_cursor
        if cursor is None:
            break
    assert len(found) == len(set(found)) == 5
    assert set(found) == ids
    with pytest.raises(ServiceError):
        await store.list("max:42", cursor=foreign.id)


@pytest.mark.asyncio
async def test_conflicting_result_rolls_back_success_and_preserves_owner(store):
    plan = sample_trip()
    await store.put(plan, "max:43")
    job = TripJobStatus(id=uuid4(), events=[],  status=JobState.RUNNING, progress=70, message="Работаем")
    await store.create_job(job, "max:42", 3)
    with pytest.raises(ValueError):
        await store.finish_job(job.id, "max:42", plan)
    assert (await store.get_job(job.id, "max:42")).status == JobState.RUNNING
    assert await store.get(plan.id, "max:42") is None
    assert await store.get(plan.id, "max:43") is not None
