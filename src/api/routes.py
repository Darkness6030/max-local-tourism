import asyncio
from datetime import date, time, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from src.auth import Identity, IdentityDep
from src.config import Settings, get_settings
from src.container import Container
from src.models import (
    DestinationSuggestion,
    GeoPoint,
    HealthResponse,
    JobState,
    OriginCity,
    PackingUpdate,
    TransportOptions,
    TripJobCreated,
    TripJobStatus,
    TripPage,
    TripPlan,
    TripRequest,
    WeatherForecast,
    current_date,
)
from src.services.destinations import RECENT_DESTINATION_LIMIT
from src.services.planner import validate_destination

router = APIRouter(prefix="/api/v1")
development_router = APIRouter(prefix="/api/v1")


@router.get("/auth/me", response_model=Identity, tags=["MAX"])
async def auth_me(identity: IdentityDep) -> Identity:
    return identity


def get_container(request: Request) -> Container:
    return request.app.state.container


ContainerDep = Annotated[Container, Depends(get_container)]


@router.get("/cities/validate", tags=["trips"])
async def validate_city(
    identity: IdentityDep,
    container: ContainerDep,
    origin: OriginCity,
    destination: Annotated[str, Query(min_length=2, max_length=160)],
) -> dict:
    city, distance = await validate_destination(container.geocoding, origin, destination)
    return {"city": city, "distance_km": round(distance, 1)}


@router.get("/health", response_model=HealthResponse, tags=["system"])
async def health(
    settings: Annotated[Settings, Depends(get_settings)],
) -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        integrations={
            "gigachat_configured": bool(settings.gigachat_credentials),
            "yandex_schedule_configured": bool(settings.yandex_schedule_api_key),
            "weather_provider": settings.selected_weather_provider,
            "openweather_configured": bool(settings.openweather_api_key),
            "geocoder": "geopy/Nominatim (ru)",
            "hotels": "OpenStreetMap / Overpass (catalog)",
            "storage": "PostgreSQL",
            "supported_origins": [city.value for city in OriginCity],
            "max_configured": bool(settings.max_bot_token),
        },
    )


@development_router.get(
    "/examples/trip-request", response_model=TripRequest, tags=["system"]
)
async def example_request() -> TripRequest:
    return TripRequest(
        origin="Москва",
        destination="Коломна",
        start_date=current_date() + timedelta(days=2),
        days=1,
        budget_rub=12_000,
        travelers=2,
        group_type="couple",
        preferences="История, архитектура и местная кухня; без слишком раннего подъёма.",
        pace="balanced",
        has_car=False,
        departure_after=time(8, 0),
        return_after=time(18, 0),
    )


@development_router.get("/geocode", response_model=GeoPoint, tags=["integrations"])
async def geocode(
    identity: IdentityDep,
    container: ContainerDep,
    query: Annotated[str, Query(min_length=2, max_length=160)],
) -> GeoPoint:
    return await container.geocoding.geocode(query)


@development_router.get(
    "/weather", response_model=WeatherForecast, tags=["integrations"]
)
async def weather(
    identity: IdentityDep,
    container: ContainerDep,
    place: Annotated[str, Query(min_length=2, max_length=160)],
    start_date: date,
    days: Annotated[int, Query(ge=1, le=3)] = 1,
) -> WeatherForecast:
    point = await container.geocoding.geocode(place)
    return await container.weather.forecast(point, start_date, days)


@development_router.get(
    "/transport", response_model=TransportOptions, tags=["integrations"]
)
async def transport(
    identity: IdentityDep,
    container: ContainerDep,
    from_place: Annotated[str, Query(min_length=2, max_length=160)],
    to_place: Annotated[str, Query(min_length=2, max_length=160)],
    travel_date: date,
    departure_after: time = time(7, 0),
    return_after: time = time(17, 0),
) -> TransportOptions:
    origin, destination = await _geocode_pair(container, from_place, to_place)
    return await container.schedule.find_round_trip(
        origin,
        destination,
        outbound_date=travel_date,
        return_date=travel_date,
        departure_after=departure_after,
        return_after=return_after,
    )


@development_router.post(
    "/destinations/suggest",
    response_model=DestinationSuggestion,
    tags=["integrations"],
)
async def suggest_destination(
    identity: IdentityDep,
    payload: TripRequest,
    container: ContainerDep,
) -> DestinationSuggestion:
    recent = await container.store.recent_destinations(identity.owner_id, RECENT_DESTINATION_LIMIT)
    return await container.gigachat.suggest_destination(payload, recent_destinations=recent)


@router.post("/trips/generate", response_model=TripPlan, tags=["trips"])
async def generate_trip(
    payload: TripRequest, container: ContainerDep, identity: IdentityDep
) -> TripPlan:
    if payload.destination:
        await validate_destination(
            container.geocoding, payload.origin, payload.destination
        )

    created = await container.jobs.submit(payload, owner_id=identity.owner_id)
    while True:
        job = await container.jobs.get(created.id, owner_id=identity.owner_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Задача больше недоступна")

        if job.status == JobState.SUCCEEDED:
            return job.result

        if job.status == JobState.FAILED:
            raise HTTPException(status_code=502, detail=job.error.error)

        await asyncio.sleep(0.1)


@router.post(
    "/trips/jobs",
    response_model=TripJobCreated,
    status_code=202,
    tags=["trips"],
)
async def create_trip_job(
    payload: TripRequest,
    container: ContainerDep,
    identity: IdentityDep,
    request: Request,
) -> TripJobCreated:
    if payload.destination:
        await validate_destination(
            container.geocoding, payload.origin, payload.destination
        )

    created = await container.jobs.submit(payload, owner_id=identity.owner_id)
    created.status_url = request.scope.get("root_path", "") + created.status_url
    return created


@router.get("/trips/jobs/{job_id}", response_model=TripJobStatus, tags=["trips"])
async def get_trip_job(
    job_id: UUID, container: ContainerDep, identity: IdentityDep
) -> TripJobStatus:
    job = await container.jobs.get(job_id, owner_id=identity.owner_id)
    if job and job.error:
        job.error.details = None

    if job is None:
        raise HTTPException(status_code=404, detail="Задача генерации не найдена")

    return job


@router.get("/trips", response_model=TripPage, tags=["trips"])
async def list_trips(
    container: ContainerDep,
    identity: IdentityDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: UUID | None = None,
) -> TripPage:
    return await container.store.list(identity.owner_id, limit=limit, cursor=cursor)


@router.get("/trips/{trip_id}", response_model=TripPlan, tags=["trips"])
async def get_trip(
    trip_id: UUID, container: ContainerDep, identity: IdentityDep
) -> TripPlan:
    trip = await container.store.get(trip_id, owner_id=identity.owner_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Поездка не найдена")

    return trip


@router.patch("/trips/{trip_id}/packing", response_model=TripPlan, tags=["trips"])
async def update_packing(
    trip_id: UUID, payload: PackingUpdate, container: ContainerDep, identity: IdentityDep
) -> TripPlan:
    trip = await container.store.set_packed(trip_id, identity.owner_id, payload.item_index, payload.checked)
    if trip is None:
        raise HTTPException(status_code=404, detail="Поездка не найдена")

    return trip


@router.get("/trips/{trip_id}/share", tags=["trips"])
async def share_trip(
    trip_id: UUID, container: ContainerDep, identity: IdentityDep
) -> dict[str, str]:
    trip = await container.store.get(trip_id, owner_id=identity.owner_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Поездка не найдена")

    return {"text": trip.share_text}


async def _geocode_pair(
    container: Container, first: str, second: str
) -> tuple[GeoPoint, GeoPoint]:
    return await asyncio.gather(
        container.geocoding.geocode(first),
        container.geocoding.geocode(second),
    )
