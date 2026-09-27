"""Durable, owner-scoped departure reminders. MAX delivery is injected for tests."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import delete, select

from src.config import Settings
from src.database import TransportReminderRecord, TripRecord
from src.errors import ServiceError
from src.models import TransportOption, TripPlan
from src.services.max_bot import max_bot

Direction = Literal["outbound", "return_trip"]
REMINDER_MINUTES = (30, 10, 0)
DELIVERY_GRACE = timedelta(minutes=1)
logger = logging.getLogger(__name__)


class ReminderUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    option_index: int | None = Field(ge=0, strict=True)


class ReminderSelection(BaseModel):
    outbound: int | None = None
    return_trip: int | None = None


class ReminderState(ReminderSelection):
    available: bool


class ReminderStore:
    def __init__(self, sessions):
        self.sessions = sessions

    async def get(self, trip_id: UUID, owner_id: str) -> ReminderSelection | None:
        async with self.sessions() as session:
            trip = await session.scalar(select(TripRecord.id).where(
                TripRecord.id == trip_id, TripRecord.owner_id == owner_id))
            if trip is None:
                return None
            rows = (await session.scalars(select(TransportReminderRecord).where(
                TransportReminderRecord.trip_id == trip_id,
                TransportReminderRecord.owner_id == owner_id))).all()
            return ReminderSelection(**{row.direction: row.option_index for row in rows})

    async def set(
        self, trip_id: UUID, owner_id: str, direction: Direction, option_index: int | None,
        *, now: datetime | None = None,
    ) -> ReminderSelection | None:
        now = now or datetime.now(timezone.utc)
        async with self.sessions.begin() as session:
            # Serialize choices, including the first choice with no reminder rows yet.
            trip = await session.scalar(select(TripRecord).where(
                TripRecord.id == trip_id, TripRecord.owner_id == owner_id).with_for_update())
            if trip is None:
                return None
            plan = TripPlan.model_validate(trip.payload)
            rows = (await session.scalars(select(TransportReminderRecord).where(
                TransportReminderRecord.trip_id == trip_id))).all()
            selection = ReminderSelection(**{row.direction: row.option_index for row in rows})
            if getattr(selection, direction) == option_index:
                return selection  # Retrying a saved choice must not resend delivered reminders.
            option = None
            if option_index is not None:
                if not owner_id.startswith("max:") or not owner_id[4:].isdigit() or int(owner_id[4:]) <= 0:
                    raise ServiceError("reminders", "Откройте приложение из MAX, чтобы включить напоминания", status_code=403)
                options = getattr(plan.transport, direction) if plan.transport else []
                if not 0 <= option_index < len(options):
                    raise ServiceError("reminders", "Рейс не найден", status_code=422)
                option = options[option_index]
                if option.departure.tzinfo is None or option.departure <= now:
                    raise ServiceError("reminders", "Этот рейс уже отправился", status_code=422)
            await session.execute(delete(TransportReminderRecord).where(
                TransportReminderRecord.trip_id == trip_id,
                TransportReminderRecord.direction == direction))
            if option is not None:
                for minutes in REMINDER_MINUTES:
                    due = option.departure - timedelta(minutes=minutes)
                    session.add(TransportReminderRecord(
                        trip_id=trip_id, owner_id=owner_id, direction=direction,
                        option_index=option_index, option=option.model_dump(mode="json"),
                        minutes_before=minutes, due_at=due,
                        next_attempt_at=due if due >= now else None,
                    ))
            setattr(selection, direction, option_index)
            return selection

    async def deliver_one(
        self, send: Callable[[TransportReminderRecord], Awaitable[None]],
        *, now: datetime | None = None,
    ) -> bool:
        now = now or datetime.now(timezone.utc)
        async with self.sessions.begin() as session:
            row = await session.scalar(select(TransportReminderRecord).where(
                TransportReminderRecord.next_attempt_at <= now,
            ).order_by(TransportReminderRecord.next_attempt_at).limit(1).with_for_update(skip_locked=True))
            if row is None:
                return False
            # The row lock prevents a replacement/disable from finishing during this send.
            if now >= row.due_at + DELIVERY_GRACE:
                row.next_attempt_at = None
                return True
            try:
                await send(row)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Reminder delivery failed: %s", type(exc).__name__)
                row.next_attempt_at = now + timedelta(seconds=15)
            else:
                row.sent_at = now
                row.next_attempt_at = None
            return True


def reminder_text(row: TransportReminderRecord) -> str:
    option = TransportOption.model_validate(row.option)
    heading = f"Отправление через {row.minutes_before} минут" if row.minutes_before else "Время отправления"
    direction = "Туда" if row.direction == "outbound" else "Обратно"
    kind = {"bus": "Автобус", "suburban": "Электричка", "train": "Поезд"}.get(option.transport_type, "Рейс")
    number = f" №{option.route_number}" if option.route_number else ""
    departure = option.departure.strftime("%d.%m в %H:%M")
    return (
        f"⏰ {heading}\n{direction}: {kind}{number}\n"
        f"{option.from_station} → {option.to_station}\nОтправление {departure} (местное время)."
    )[:4000]


async def send_reminder(settings: Settings, row: TransportReminderRecord) -> None:
    async with max_bot(settings) as bot:
        result = await bot.send_message(user_id=int(row.owner_id.removeprefix("max:")),
                                        text=reminder_text(row), notify=True)
        if not result or not result.message.body.mid:
            raise ServiceError("max", "Не удалось отправить напоминание", status_code=503)


class ReminderWorker:
    def __init__(self, store: ReminderStore, settings: Settings):
        self.store = store
        self.settings = settings
        self.task: asyncio.Task | None = None

    def start(self):
        if self.settings.max_bot_token:
            self.task = asyncio.create_task(self.run(), name="transport-reminders")

    async def close(self):
        if self.task:
            self.task.cancel()
            await asyncio.gather(self.task, return_exceptions=True)

    async def run(self):
        async def send(row):
            await send_reminder(self.settings, row)

        while True:
            try:
                processed = await self.store.deliver_one(send)
            except Exception as exc:  # noqa: BLE001
                logger.error("Reminder worker failed: %s", type(exc).__name__)
                processed = False
            # Stay below MAX's two messages/second even for multiple trips of one user.
            await asyncio.sleep(0.6 if processed else 5)
