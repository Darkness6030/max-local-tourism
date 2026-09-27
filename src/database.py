"""PostgreSQL / asyncpg / SQLModel, with one AsyncSession per operation."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import Field, SQLModel


class UserProfileRecord(SQLModel, table=True):
    __tablename__ = "user_profiles"
    owner_id: str = Field(sa_column=Column(String(80), primary_key=True))
    onboarding_completed_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))


class TripRecord(SQLModel, table=True):
    __tablename__ = "trips"
    __table_args__ = (Index("ix_trips_owner_created_id", "owner_id", "created_at", "id"),)
    id: UUID = Field(sa_column=Column(Uuid, primary_key=True))
    owner_id: str = Field(sa_column=Column(String(80), nullable=False))
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    payload: dict = Field(sa_column=Column(JSONB, nullable=False))


class SharedTripRecord(SQLModel, table=True):
    __tablename__ = "shared_trips"
    token: UUID = Field(sa_column=Column(Uuid, primary_key=True))
    source_id: UUID = Field(sa_column=Column(
        Uuid, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, unique=True))


class SharedTripImportRecord(SQLModel, table=True):
    __tablename__ = "shared_trip_imports"
    token: UUID = Field(sa_column=Column(
        Uuid, ForeignKey("shared_trips.token", ondelete="CASCADE"), primary_key=True))
    owner_id: str = Field(sa_column=Column(String(80), primary_key=True))
    trip_id: UUID = Field(sa_column=Column(
        Uuid, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False))


class JobRecord(SQLModel, table=True):
    __tablename__ = "trip_jobs"
    __table_args__ = (
        Index("ix_jobs_owner_created", "owner_id", "created_at"),
        Index("uq_jobs_active_owner", "owner_id", unique=True,
              postgresql_where=text("status IN ('queued', 'running')")),
    )
    id: UUID = Field(sa_column=Column(Uuid, primary_key=True))
    owner_id: str = Field(sa_column=Column(String(80), nullable=False))
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    status: str = Field(sa_column=Column(String(16), nullable=False))
    payload: dict = Field(sa_column=Column(JSONB, nullable=False))
    trip_id: UUID | None = Field(default=None, sa_column=Column(
        Uuid, ForeignKey("trips.id", ondelete="CASCADE"), nullable=True, unique=True))


def database_url(raw: str):
    url = make_url(raw)
    if url.drivername == "postgresql":
        url = url.set(drivername="postgresql+asyncpg")
    if url.drivername != "postgresql+asyncpg":
        raise ValueError("DATABASE_URL должен указывать на PostgreSQL с asyncpg")
    return url


class Database:
    def __init__(self, url: str):
        self.engine = create_async_engine(
            database_url(url), pool_pre_ping=True, pool_size=5, max_overflow=5,
            echo=False, hide_parameters=True,
        )

        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)
        self._worker_connection = None

    async def initialize(self):
        # Create missing tables; changes to existing tables require a migration.
        async with self.engine.begin() as connection:
            await connection.execute(text("SELECT pg_advisory_xact_lock(759603986)"))
            await connection.run_sync(SQLModel.metadata.create_all)

    async def acquire_worker(self):
        # Only one generation worker may recover unfinished jobs at startup.
        connection = await self.engine.connect()
        acquired = await connection.scalar(text("SELECT pg_try_advisory_lock(759603984)"))
        if not acquired:
            await connection.close()
            raise RuntimeError("БД уже обслуживается другим процессом генерации")

        await connection.commit()
        self._worker_connection = connection

    async def close(self):
        if self._worker_connection is not None:
            await self._worker_connection.execute(text("SELECT pg_advisory_unlock(759603984)"))
            await self._worker_connection.close()
            self._worker_connection = None

        await self.engine.dispose()


class TransportReminderRecord(SQLModel, table=True):
    __tablename__ = "transport_reminders"
    __table_args__ = (Index("ix_transport_reminders_due", "next_attempt_at"),)
    trip_id: UUID = Field(sa_column=Column(
        Uuid, ForeignKey("trips.id", ondelete="CASCADE"), primary_key=True))
    direction: str = Field(sa_column=Column(String(16), primary_key=True))
    minutes_before: int = Field(primary_key=True)
    owner_id: str = Field(sa_column=Column(String(80), nullable=False))
    option_index: int
    option: dict = Field(sa_column=Column(JSONB, nullable=False))
    due_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    next_attempt_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    sent_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
