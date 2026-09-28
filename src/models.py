from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)

from src.cities import CityName, EnabledOrigin, default_origin
from src.constants import (
    MAX_FORECAST_DAYS,
    MAX_TRIP_DAYS,
    MSK_TIMEZONE,
    SOURCE_NOMINATIM,
    SOURCE_YANDEX,
    SUGGESTED_CITY_DISTANCE_KM,
    YANDEX_SCHEDULE_SITE_URL,
)


def default_trip_date() -> date:
    return current_date() + timedelta(days=1)


def current_date() -> date:
    return datetime.now(MSK_TIMEZONE).date()


class GroupType(StrEnum):
    SOLO = "solo"
    COUPLE = "couple"
    FRIENDS = "friends"
    FAMILY = "family"


class Pace(StrEnum):
    RELAXED = "relaxed"
    BALANCED = "balanced"
    INTENSIVE = "intensive"


class ProfilePreferences(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    display_name: str = Field(default="", max_length=60)
    avatar_style: Literal["max", "initials", "compass", "mountain", "sun"] = "max"
    avatar_color: Literal["lavender", "sage", "peach", "sky"] = "lavender"
    # Legacy appearance fields remain readable for older clients; current UI uses MAX identity.
    max_distance_km: int = Field(default=SUGGESTED_CITY_DISTANCE_KM, ge=300, le=600)
    preferred_transport: Literal["bus", "suburban", "car"] = "suburban"
    origin: CityName = Field(default_factory=default_origin)
    pace: Pace = Pace.BALANCED
    interests: list[Literal["Природа", "История", "Местная кухня", "Прогулки", "Активный отдых", "Музеи"]] = Field(
        default_factory=lambda: ["Прогулки", "Местная кухня"], max_length=6)

    @field_validator("display_name")
    @classmethod
    def name_without_controls(cls, value: str) -> str:
        if any(ord(char) < 32 for char in value):
            raise ValueError("Имя не должно содержать управляющие символы")
        return value

    @field_validator("interests")
    @classmethod
    def unique_interests(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(value))


class ProfilePreferencesUpdate(ProfilePreferences):
    """Only enabled cities may be selected in new profile writes."""

    origin: EnabledOrigin = Field(default_factory=default_origin)


class UserProfile(BaseModel):
    onboarding_completed: bool
    preferences: ProfilePreferences = Field(default_factory=ProfilePreferences)


class TripParameters(BaseModel):
    """Saved request snapshot: historical dates remain readable."""
    model_config = ConfigDict(extra="forbid")

    origin: CityName = Field(default_factory=default_origin)
    destination: str | None = Field(
        default=None,
        min_length=2,
        max_length=160,
        description="Если не задано, направление предложит ИИ.",
        examples=["Коломна"],
    )

    start_date: date = Field(default_factory=default_trip_date)
    days: int = Field(default=1, ge=1, le=MAX_TRIP_DAYS)
    budget_rub: int = Field(default=12_000, ge=1_000, le=1_000_000)
    travelers: int = Field(default=2, ge=1, le=20)
    group_type: GroupType = GroupType.COUPLE
    children_ages: list[int] = Field(default_factory=list, max_length=10)
    preferences: str = Field(
        default="История, архитектура, местная кухня; без слишком раннего подъёма.",
        min_length=3,
        max_length=1500,
        description="Интересы и пожелания пользователя в свободной форме.",
    )

    pace: Pace = Pace.BALANCED
    has_car: bool = False
    max_distance_km: int = Field(default=SUGGESTED_CITY_DISTANCE_KM, ge=300, le=600)
    preferred_transport: Literal["bus", "suburban", "car"] | None = None
    departure_after: time = time(7, 0)
    return_after: time = time(17, 0)
    max_travel_minutes: int = Field(default=240, ge=30, le=720)

    @model_validator(mode="after")
    def validate_group(self) -> TripParameters:
        if self.preferred_transport is not None:
            self.has_car = self.preferred_transport == "car"
        if any(age < 0 or age > 17 for age in self.children_ages):
            raise ValueError("возраст ребёнка должен быть от 0 до 17 лет")

        if self.children_ages and self.group_type != GroupType.FAMILY:
            raise ValueError("children_ages допустим только для group_type=family")

        return self


class TripRequest(TripParameters):
    """New generation requests must fit the available forecast horizon."""

    origin: EnabledOrigin = Field(default_factory=default_origin)

    @model_validator(mode="after")
    def validate_scenario(self) -> TripRequest:
        today = current_date()
        if self.start_date < today:
            raise ValueError("start_date не может быть в прошлом")

        if self.start_date + timedelta(days=self.days - 1) >= today + timedelta(days=MAX_FORECAST_DAYS):
            raise ValueError(f"прогноз доступен максимум на {MAX_FORECAST_DAYS} дней вперёд")

        return self


class Coordinates(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class GeoPoint(Coordinates):
    query: str
    title: str
    address: str
    source: str = SOURCE_NOMINATIM
    wikipedia_title: str | None = None


class WeatherDay(BaseModel):
    date: date
    description: str
    temperature_min_c: float
    temperature_max_c: float
    precipitation_probability_percent: int | None = Field(default=None, ge=0, le=100)
    precipitation_mm: float | None = Field(default=None, ge=0)
    wind_max_ms: float | None = Field(default=None, ge=0)


class WeatherForecast(BaseModel):
    provider: str
    location: str
    timezone: str | None = None
    days: list[WeatherDay]
    source_url: HttpUrl


class SettlementRef(BaseModel):
    code: str
    title: str
    distance_km: float | None = None


class TransportOption(BaseModel):
    departure: datetime
    arrival: datetime
    duration_minutes: int = Field(ge=0)
    from_station: str
    to_station: str
    from_station_code: str | None = None
    to_station_code: str | None = None
    from_station_coordinates: Coordinates | None = None
    to_station_coordinates: Coordinates | None = None
    transport_type: str
    vehicle: str | None = None
    route_number: str | None = None
    route_title: str | None = None
    carrier: str | None = None
    has_transfers: bool = False
    price_rub: float | None = Field(default=None, ge=0)
    buy_url: HttpUrl
    map_url: HttpUrl | None = None


class TransportOptions(BaseModel):
    origin: SettlementRef
    destination: SettlementRef
    outbound: list[TransportOption]
    return_trip: list[TransportOption]
    source_name: str = SOURCE_YANDEX
    source_url: HttpUrl = Field(default=YANDEX_SCHEDULE_SITE_URL, validate_default=True)


class DestinationSuggestion(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    region: str = Field(min_length=2, max_length=100)
    reason: str = Field(min_length=10, max_length=500)


class TimelineItem(BaseModel):
    start_time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    end_time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    title: str = Field(min_length=2, max_length=160)
    place: str = Field(min_length=2, max_length=200)
    description: str = Field(min_length=5, max_length=800)
    indoor: bool
    estimated_cost_rub: int = Field(default=0, ge=0)

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def normalize_time(cls, value: object) -> object:
        """ИИ может вернуть HH:MM:SS; публичный формат всегда HH:MM."""
        if not isinstance(value, str):
            return value
        try:
            return time.fromisoformat(value).strftime("%H:%M")
        except ValueError:
            return value


class ItineraryDay(BaseModel):
    date: date
    title: str
    items: list[TimelineItem] = Field(min_length=2, max_length=12)


class BudgetItem(BaseModel):
    category: str
    amount_rub: int = Field(ge=0)
    comment: str | None = None


class GeneratedTripContent(BaseModel):
    title: str = Field(min_length=4, max_length=160)
    summary: str = Field(min_length=20, max_length=1200)
    itinerary: list[ItineraryDay] = Field(min_length=1, max_length=3)
    budget_items: list[BudgetItem] = Field(min_length=1, max_length=10)
    outbound_fare_rub: int | None = Field(ge=0, description="Оценка билета туда на одного человека, без льгот; null, если оценить нельзя")
    return_fare_rub: int | None = Field(ge=0, description="Оценка обратного билета на одного человека, без льгот; null, если оценить нельзя")
    lodging_nightly_rub: int | None = Field(default=None, ge=0)
    weather_advice: str = Field(min_length=10, max_length=800)
    packing_list: list[str] = Field(min_length=1, max_length=20)
    notes: list[str] = Field(default_factory=list, max_length=12)


class BudgetSummary(BaseModel):
    limit_rub: int
    estimated_total_rub: int
    per_person_rub: int
    within_budget: bool
    items: list[BudgetItem]


class CityPhoto(BaseModel):
    url: HttpUrl
    source_url: HttpUrl
    article_url: HttpUrl
    author: str


class Hotel(Coordinates):
    id: str
    name: str
    kind: Literal["hotel", "guest_house"]
    address: str | None = None
    distance_km: float = Field(ge=0)
    website: HttpUrl | None = None
    map_url: HttpUrl
    source_url: HttpUrl


class Accommodation(BaseModel):
    check_in: date
    check_out: date
    nights: int = Field(ge=1)
    rooms: int = Field(ge=1)
    estimated_room_night_rub: int = Field(ge=0)
    estimated_total_rub: int = Field(ge=0)
    status: Literal["found", "empty", "unavailable"]
    hotels: list[Hotel] = Field(default_factory=list)
    search_url: HttpUrl
    fetched_at: datetime | None = None


class TripPlan(BaseModel):
    id: UUID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request: TripParameters
    title: str
    summary: str
    estimated_travel_minutes: int | None = Field(default=None, ge=0)
    destination_reason: str | None = None
    destination_photo: CityPhoto | None = None
    accommodation: Accommodation | None = None
    origin: GeoPoint
    destination: GeoPoint
    weather: WeatherForecast
    transport: TransportOptions | None
    itinerary: list[ItineraryDay]
    budget: BudgetSummary
    weather_advice: str
    packing_list: list[str]
    packed_items: list[int] = Field(default_factory=list)
    notes: list[str]
    map_url: HttpUrl | None = None
    share_text: str
    warnings: list[str] = Field(default_factory=list)
    sources: list[dict[str, str]]


class PackingUpdate(BaseModel):
    item_index: int = Field(ge=0, strict=True)
    checked: bool = Field(strict=True)


class HealthResponse(BaseModel):
    status: str
    version: str
    integrations: dict[str, Any]


class TripSummary(BaseModel):
    destination_photo: CityPhoto | None = None
    id: UUID
    created_at: datetime
    title: str
    origin: str
    destination: str
    start_date: date
    days: int
    travelers: int
    estimated_total_rub: int


class TripPage(BaseModel):
    items: list[TripSummary]
    total: int
    next_cursor: UUID | None = None


class ErrorBody(BaseModel):
    error: str
    service: str | None = None
    details: str | None = None


class JobState(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ProgressEvent(BaseModel):
    progress: int = Field(ge=0, le=100)
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TripJobCreated(BaseModel):
    id: UUID
    status: JobState = JobState.QUEUED
    status_url: str


class TripJobStatus(BaseModel):
    id: UUID
    status: JobState
    progress: int = Field(ge=0, le=100)
    message: str
    events: list[ProgressEvent]
    result: TripPlan | None = None
    error: ErrorBody | None = None
