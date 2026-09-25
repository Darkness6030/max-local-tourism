from __future__ import annotations

import asyncio
import logging
from uuid import UUID, uuid4

from src.errors import ServiceError
from src.models import (
    ErrorBody,
    JobState,
    ProgressEvent,
    TripJobCreated,
    TripJobStatus,
    TripRequest,
)
from src.services.destinations import RECENT_DESTINATION_LIMIT
from src.services.planner import TripPlanner
from src.store import TripStore

logger = logging.getLogger(__name__)


class TripJobManager:
    """One generation worker; durable progress and atomic result commit in PostgreSQL."""

    def __init__(self, planner: TripPlanner, store: TripStore, max_active: int = 3):
        self.planner = planner
        self.store = store
        self.max_active = max_active
        self._tasks: set[asyncio.Task[None]] = set()

    async def submit(self, request: TripRequest, owner_id: str | None = None) -> TripJobCreated:
        owner = owner_id or "internal"
        event = ProgressEvent(progress=0, message="Запрос поставлен в очередь")
        job = TripJobStatus(id=uuid4(), status=JobState.QUEUED, progress=0, message=event.message, events=[event])
        await self.store.create_job(job, owner, self.max_active)
        task = asyncio.create_task(self._run(job, request, owner), name=f"trip-job-{job.id}")
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return TripJobCreated(id=job.id, status_url=f"/api/v1/trips/jobs/{job.id}")

    async def get(self, job_id: UUID, owner_id: str | None = None) -> TripJobStatus | None:
        return await self.store.get_job(job_id, owner_id or "internal")

    async def close(self):
        tasks = tuple(self._tasks)
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _run(self, job: TripJobStatus, request: TripRequest, owner: str):
        async def report(progress: int, message: str):
            # 100% means committed, not merely returned by the provider.
            job.progress = min(progress, 99)
            job.message = message
            job.events.append(ProgressEvent(progress=job.progress, message=message))
            await self.store.update_job(job, owner)

        try:
            job.status = JobState.RUNNING
            await report(1, "Генерация запущена")
            async with asyncio.timeout(360):
                recent = await self.store.recent_destinations(owner, RECENT_DESTINATION_LIMIT) if not request.destination else []
                result = await self.planner.generate(request, progress=report, recent_destinations=recent)
            await self.store.finish_job(job.id, owner, result)
        except asyncio.CancelledError:
            # On restart, recover_interrupted_jobs converts this durable state to failed.
            raise
        except TimeoutError:
            await self._fail(job, owner, "Генерация заняла слишком много времени. Попробуйте ещё раз.", "planner")
        except ServiceError as exc:
            await self._fail(job, owner, exc.message, exc.service)
        except Exception as exc:  # noqa: BLE001
            logger.error("Trip job %s failed with %s", job.id, type(exc).__name__)
            await self._fail(job, owner, "Не удалось сохранить поездку. Попробуйте ещё раз.", "backend")

    async def _fail(self, job, owner, message, service):
        job.status = JobState.FAILED
        job.message = message
        job.error = ErrorBody(error=message, service=service)
        job.events.append(ProgressEvent(progress=job.progress, message=message))

        try:
            await self.store.update_job(job, owner)
        except Exception as exc:  # noqa: BLE001
            logger.error("Could not persist failure for %s: %s", job.id, type(exc).__name__)
