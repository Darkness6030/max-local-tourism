from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import delete, func, select, text, tuple_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.database import (
    JobRecord,
    SharedTripImportRecord,
    SharedTripRecord,
    TripRecord,
    UserProfileRecord,
)
from src.errors import ServiceError
from src.models import (
    ErrorBody,
    JobState,
    TripJobStatus,
    TripPage,
    TripPlan,
    TripSummary,
    UserProfile,
)

ACTIVE_JOB_STATES = (JobState.QUEUED, JobState.RUNNING)


class TripStore:
    """Durable owner-scoped trips and jobs. Completed trips are never evicted."""

    def __init__(self, sessions: async_sessionmaker):
        self.sessions = sessions

    async def get_profile(self, owner_id: str) -> UserProfile:
        async with self.sessions() as session:
            row = await session.get(UserProfileRecord, owner_id)
            return UserProfile(onboarding_completed=row is not None)

    async def complete_onboarding(self, owner_id: str) -> UserProfile:
        async with self.sessions.begin() as session:
            await session.execute(
                insert(UserProfileRecord)
                .values(owner_id=owner_id, onboarding_completed_at=datetime.now(timezone.utc))
                .on_conflict_do_nothing(index_elements=["owner_id"])
            )
        return UserProfile(onboarding_completed=True)

    @staticmethod
    async def _put(session, plan: TripPlan, owner_id: str):
        payload = plan.model_dump(mode="json", exclude={"packed_items"})
        await session.execute(
            insert(TripRecord)
            .values(
                id=plan.id,
                owner_id=owner_id,
                created_at=plan.created_at,
                payload={**payload, "packed_items": []},
            )
            .on_conflict_do_nothing(index_elements=["id"])
        )

        row = await session.scalar(select(TripRecord).where(TripRecord.id == plan.id).with_for_update())
        if row.owner_id != owner_id:
            raise ValueError("Trip ID belongs to a different owner")

        existing = TripPlan.model_validate(row.payload).model_dump(mode="json", exclude={"packed_items"})
        if existing != payload:
            # Any change to the plan invalidates the previous checklist.
            row.payload = {**payload, "packed_items": []}
            row.created_at = plan.created_at

    async def put(self, plan: TripPlan, owner_id: str | None = None):
        async with self.sessions.begin() as session:
            await self._put(session, plan, owner_id or "internal")

    async def get(self, trip_id: UUID, owner_id: str | None = None) -> TripPlan | None:
        async with self.sessions() as session:
            row = await session.scalar(
                select(TripRecord).where(
                    TripRecord.id == trip_id, TripRecord.owner_id == (owner_id or "internal")
                )
            )
            return TripPlan.model_validate(row.payload) if row else None

    async def publish_share(self, trip_id: UUID, owner_id: str) -> UUID | None:
        async with self.sessions.begin() as session:
            source = await session.scalar(select(TripRecord).where(
                TripRecord.id == trip_id, TripRecord.owner_id == owner_id,
            ).with_for_update())
            if source is None:
                return None
            imported_token = await session.scalar(select(SharedTripImportRecord.token).where(
                SharedTripImportRecord.trip_id == trip_id,
                SharedTripImportRecord.owner_id == owner_id,
            ))
            if imported_token:
                return imported_token
            await session.execute(insert(SharedTripRecord).values(
                token=uuid4(), source_id=trip_id,
            ).on_conflict_do_nothing(index_elements=["source_id"]))
            return await session.scalar(select(SharedTripRecord.token).where(
                SharedTripRecord.source_id == trip_id,
            ))

    async def import_share(self, token: UUID, owner_id: str) -> TripPlan | None:
        async with self.sessions.begin() as session:
            # Serialize repeated/concurrent imports and imports through forwarded copies.
            shared = await session.scalar(select(SharedTripRecord).where(
                SharedTripRecord.token == token,
            ).with_for_update())
            if shared is None:
                return None
            source = await session.get(TripRecord, shared.source_id)
            if source.owner_id == owner_id:
                return TripPlan.model_validate(source.payload)
            imported = await session.get(SharedTripImportRecord, (token, owner_id))
            if imported:
                row = await session.get(TripRecord, imported.trip_id)
                return TripPlan.model_validate(row.payload)
            plan = TripPlan.model_validate(source.payload).model_copy(update={
                "id": uuid4(), "packed_items": [],
            })
            await self._put(session, plan, owner_id)
            session.add(SharedTripImportRecord(token=token, owner_id=owner_id, trip_id=plan.id))
            # Forwarding a copy uses the same link, avoiding duplicate routes.
            return plan

    async def recent_destinations(self, owner_id: str, limit: int) -> list[str]:
        async with self.sessions() as session:
            names = await session.scalars(
                select(TripRecord.payload["destination"]["title"].astext)
                .where(TripRecord.owner_id == owner_id)
                .order_by(TripRecord.created_at.desc(), TripRecord.id.desc())
                .limit(limit)
            )
            return [name for name in names if name]

    async def set_packed(
        self, trip_id: UUID, owner_id: str, item_index: int, checked: bool
    ) -> TripPlan | None:
        async with self.sessions.begin() as session:
            row = await session.scalar(
                select(TripRecord)
                .where(TripRecord.id == trip_id, TripRecord.owner_id == owner_id)
                .with_for_update()
            )
            if row is None:
                return None

            plan = TripPlan.model_validate(row.payload)
            if not 0 <= item_index < len(plan.packing_list):
                raise ServiceError("storage", "Пункт чеклиста не найден", status_code=422)

            packed = set(plan.packed_items)
            if checked:
                packed.add(item_index)
            else:
                packed.discard(item_index)

            plan.packed_items = sorted(packed)
            row.payload = plan.model_dump(mode="json")
            return plan

    async def list(self, owner_id: str, limit: int = 20, cursor: UUID | None = None) -> TripPage:
        async with self.sessions() as session:
            query = select(TripRecord).where(TripRecord.owner_id == owner_id)
            if cursor:
                anchor = await session.scalar(
                    select(TripRecord).where(TripRecord.id == cursor, TripRecord.owner_id == owner_id)
                )
                if anchor is None:
                    raise ServiceError("storage", "Список изменился. Обновите поездки.", status_code=404)
                query = query.where(
                    tuple_(TripRecord.created_at, TripRecord.id) < (anchor.created_at, anchor.id)
                )

            rows = (
                await session.scalars(
                    query.order_by(TripRecord.created_at.desc(), TripRecord.id.desc()).limit(limit + 1)
                )
            ).all()
            total = await session.scalar(
                select(func.count()).select_from(TripRecord).where(TripRecord.owner_id == owner_id)
            )

            items = []
            for row in rows[:limit]:
                plan = TripPlan.model_validate(row.payload)
                items.append(
                    TripSummary(
                        destination_photo=plan.destination_photo,
                        id=plan.id,
                        created_at=plan.created_at,
                        title=plan.title,
                        origin=plan.origin.title,
                        destination=plan.destination.title,
                        start_date=plan.request.start_date,
                        days=plan.request.days,
                        travelers=plan.request.travelers,
                        estimated_total_rub=plan.budget.estimated_total_rub,
                    )
                )

            return TripPage(items=items, total=total, next_cursor=items[-1].id if len(rows) > limit else None)

    async def delete(self, trip_id: UUID, owner_id: str) -> bool:
        async with self.sessions.begin() as session:
            result = await session.execute(
                delete(TripRecord)
                .where(TripRecord.id == trip_id, TripRecord.owner_id == owner_id)
                .returning(TripRecord.id)
            )
            return result.scalar_one_or_none() is not None

    async def create_job(self, job: TripJobStatus, owner_id: str, max_active: int):
        async with self.sessions.begin() as session:
            await session.execute(text("SELECT pg_advisory_xact_lock(759603985)"))
            owners = (
                await session.scalars(
                    select(JobRecord.owner_id).where(JobRecord.status.in_(ACTIVE_JOB_STATES))
                )
            ).all()
            if len(owners) >= max_active or owner_id in owners:
                raise ServiceError(
                    "planner",
                    "Генерация уже выполняется. Дождитесь результата и попробуйте ещё раз.",
                    status_code=429,
                )

            session.add(
                JobRecord(
                    id=job.id,
                    owner_id=owner_id,
                    created_at=datetime.now(timezone.utc),
                    status=job.status,
                    payload=job.model_dump(mode="json", exclude={"result"}),
                )
            )

    async def get_job(self, job_id: UUID, owner_id: str) -> TripJobStatus | None:
        async with self.sessions() as session:
            row = await session.scalar(
                select(JobRecord).where(JobRecord.id == job_id, JobRecord.owner_id == owner_id)
            )
            if row is None:
                return None

            job = TripJobStatus.model_validate(row.payload)
            if row.trip_id:
                trip = await session.scalar(
                    select(TripRecord).where(TripRecord.id == row.trip_id, TripRecord.owner_id == owner_id)
                )
                if trip is None:
                    return None
                job.result = TripPlan.model_validate(trip.payload)
            return job

    async def update_job(self, job: TripJobStatus, owner_id: str):
        async with self.sessions.begin() as session:
            row = await session.scalar(
                select(JobRecord)
                .where(JobRecord.id == job.id, JobRecord.owner_id == owner_id)
                .with_for_update()
            )
            if row is None or row.status not in ACTIVE_JOB_STATES:
                return

            row.status = job.status
            row.payload = job.model_dump(mode="json", exclude={"result"})

    async def finish_job(self, job_id: UUID, owner_id: str, plan: TripPlan):
        async with self.sessions.begin() as session:
            row = await session.scalar(
                select(JobRecord)
                .where(JobRecord.id == job_id, JobRecord.owner_id == owner_id)
                .with_for_update()
            )
            if row is None or row.status not in ACTIVE_JOB_STATES:
                raise ValueError("Job is no longer active")

            await self._put(session, plan, owner_id)

            job = TripJobStatus.model_validate(row.payload)
            job.status = JobState.SUCCEEDED
            job.progress = 100
            job.message = "Поездка готова и сохранена"
            row.status = job.status
            row.payload = job.model_dump(mode="json", exclude={"result"})
            row.trip_id = plan.id

    async def recover_interrupted_jobs(self):
        async with self.sessions.begin() as session:
            rows = (
                await session.scalars(select(JobRecord).where(JobRecord.status.in_(ACTIVE_JOB_STATES)))
            ).all()
            for row in rows:
                job = TripJobStatus.model_validate(row.payload)
                job.status = JobState.FAILED
                job.message = "Генерация прервалась при перезапуске. Запустите её ещё раз; сохранённые поездки доступны в истории."
                job.error = ErrorBody(error=job.message, service="planner")
                row.status = job.status
                row.payload = job.model_dump(mode="json", exclude={"result"})
