import asyncio

import pytest

from src.errors import ServiceError
from src.jobs import TripJobManager
from src.models import JobState, TripRequest


class FailingPlanner:
    async def generate(self, request, progress, recent_destinations=None):
        await progress(35, "Точки маршрута определены")
        await progress(68, "GigaChat составляет программу")
        raise ServiceError(
            "gigachat", "Некорректный ответ модели", details="validation"
        )


@pytest.mark.asyncio
async def test_job_manager_exposes_incremental_progress_and_error(store) -> None:
    manager = TripJobManager(FailingPlanner(), store)
    created = await manager.submit(TripRequest())

    for _ in range(200):
        job = await manager.get(created.id)
        if job and job.status == JobState.FAILED:
            break
        await asyncio.sleep(0.01)

    assert job is not None
    assert job.status == JobState.FAILED
    assert [event.progress for event in job.events][:4] == [0, 1, 35, 68]
    assert job.error is not None
    assert job.error.service == "gigachat"
    await manager.close()
