from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import timedelta
from typing import TypeVar
from uuid import uuid4

from src.constants import (
    ESTIMATED_REGIONAL_SPEED_KMH,
    GIGACHAT_SITE_URL,
    MAX_CITY_DISTANCE_KM,
    MIN_CITY_DISTANCE_KM,
    NOMINATIM_SITE_URL,
    OSM_COPYRIGHT_URL,
    SOURCE_YANDEX,
    YANDEX_SCHEDULE_SITE_URL,
)
from src.errors import ServiceError
from src.models import (
    DestinationSuggestion,
    GeneratedTripContent,
    GeoPoint,
    TransportOption,
    TransportOptions,
    TripPlan,
    TripRequest,
    WeatherForecast,
)
from src.routing import build_yandex_map_url, distance_km
from src.services.budget import build_budget
from src.services.city_photos import CityPhotoService
from src.services.geocoding import GeocodingService
from src.services.gigachat_ai import GigaChatService
from src.services.hotels import HotelService
from src.services.weather import WeatherService
from src.services.yandex_schedule import YandexScheduleService

ProgressCallback = Callable[[int, str], Awaitable[None]]
ResultT = TypeVar("ResultT")


async def _noop_progress(_: int, __: str) -> None:
    return None


class TripPlanner:
    def __init__(
        self,
        *,
        geocoding: GeocodingService,
        weather: WeatherService,
        schedule: YandexScheduleService,
        gigachat: GigaChatService,
        photos: CityPhotoService | None = None,
        hotels: HotelService | None = None,
    ) -> None:
        self.geocoding = geocoding
        self.weather = weather
        self.schedule = schedule
        self.gigachat = gigachat
        self.photos = photos
        self.hotels = hotels

    async def generate(
        self,
        request: TripRequest,
        progress: ProgressCallback | None = None,
        recent_destinations: list[str] | None = None,
    ) -> TripPlan:
        report = progress or _noop_progress
        await report(5, "Определяем точки маршрута")
        destination_suggestion: DestinationSuggestion | None = None
        if request.destination:
            origin, destination = await asyncio.gather(
                self.geocoding.geocode(request.origin),
                self.geocoding.geocode(request.destination),
            )
        else:
            origin = await self.geocoding.geocode(request.origin)
            await report(15, "ИИ подбирает направление")
            destination_suggestion = await self.gigachat.suggest_destination(request, recent_destinations=recent_destinations)
            await report(28, f"Выбрано направление: {destination_suggestion.name}")
            destination = await self.geocoding.geocode(
                f"{destination_suggestion.name}, {destination_suggestion.region}, Россия"
            )

        await report(35, f"Маршрут: {origin.title} → {destination.title}")
        distance_km = round(validate_city_distance(origin, destination))

        await report(42, "Загружаем погоду и расписание")
        weather_result, transport_result, photo, catalog = await asyncio.gather(
            self.weather.forecast(destination, request.start_date, request.days),
            self.schedule.find_round_trip(
                origin,
                destination,
                outbound_date=request.start_date,
                return_date=request.start_date + timedelta(days=request.days - 1),
                departure_after=request.departure_after,
                return_after=request.return_after,
            ),
            self.photos.for_city(destination)
            if self.photos
            else asyncio.sleep(0, result=None),
            self.hotels.for_city(destination)
            if self.hotels and request.days > 1
            else asyncio.sleep(0, result=None),
            return_exceptions=True,
        )

        if isinstance(weather_result, BaseException):
            if isinstance(weather_result, ServiceError):
                raise weather_result

            raise ServiceError(
                "weather", "Не удалось получить погоду", details=str(weather_result)
            )

        transport, warnings = _resolve_transport(transport_result)
        estimated_travel_minutes = round(distance_km / ESTIMATED_REGIONAL_SPEED_KMH * 60)

        await report(62, "Погода, станции и транспорт получены")
        facts = _planning_facts(
            distance_km=distance_km,
            origin=origin,
            destination=destination,
            weather=weather_result,
            transport=transport,
            warnings=warnings,
        )

        await report(68, "ИИ составляет программу и бюджет")
        generated = await _with_heartbeat(
            self.gigachat.build_trip(
                request,
                destination_name=destination.title,
                facts=facts,
            ),
            report,
        )

        await report(90, "Проверяем и собираем результат")
        self._normalize_generated_dates(generated, request)

        budget, accommodation = build_budget(
            generated, request, destination,
            None if isinstance(catalog, BaseException) else catalog,
        )
        map_url = _plan_map_url(
            origin,
            destination,
            transport,
            by_car=request.has_car,
        )
        share_text = _share_text(
            generated=generated,
            request=request,
            destination=destination,
            map_url=map_url,
        )

        plan = TripPlan(
            id=uuid4(),
            request=request,
            title=generated.title,
            summary=generated.summary,
            destination_reason=(
                destination_suggestion.reason if destination_suggestion else None
            ),
            origin=origin,
            destination=destination,
            destination_photo=None if isinstance(photo, BaseException) else photo,
            weather=weather_result,
            transport=transport,
            accommodation=accommodation,
            itinerary=generated.itinerary,
            budget=budget,
            weather_advice=generated.weather_advice,
            packing_list=generated.packing_list,
            notes=generated.notes,
            estimated_travel_minutes=estimated_travel_minutes,
            map_url=map_url,
            share_text=share_text,
            warnings=warnings,
            sources=_sources(weather_result) + (
                [{"name": "© OpenStreetMap contributors · ODbL", "url": OSM_COPYRIGHT_URL}]
                if accommodation else []
            ),
        )

        await report(100, "Сценарий готов")
        return plan

    @staticmethod
    def _normalize_generated_dates(
        generated: GeneratedTripContent, request: TripRequest
    ) -> None:
        if len(generated.itinerary) != request.days:
            raise ServiceError(
                "gigachat",
                f"ИИ вернул {len(generated.itinerary)} дн. вместо {request.days}",
            )

        for offset, day in enumerate(generated.itinerary):
            day.date = request.start_date + timedelta(days=offset)


def validate_city_distance(origin: GeoPoint, destination: GeoPoint) -> float:
    distance = distance_km(origin, destination)
    if distance < MIN_CITY_DISTANCE_KM:
        raise ServiceError(
            "planner",
            "Этот город совпадает с точкой отправления",
            status_code=422,
        )
    if distance >= MAX_CITY_DISTANCE_KM:
        raise ServiceError(
            "planner",
            "Этот город слишком далеко",
            status_code=422,
        )
    return distance


async def validate_destination(
    geocoding: GeocodingService, origin: str, destination: str
) -> tuple[GeoPoint, float]:
    first, second = await asyncio.gather(
        geocoding.geocode(origin), geocoding.geocode(destination)
    )
    distance = validate_city_distance(first, second)
    return second, distance


def _resolve_transport(
    result: TransportOptions | BaseException,
) -> tuple[TransportOptions | None, list[str]]:
    if isinstance(result, BaseException):
        return None, [f"Транспорт не загружен: {result}"]

    return result, []


def _planning_facts(
    *,
    distance_km: int,
    origin: GeoPoint,
    destination: GeoPoint,
    weather: WeatherForecast,
    transport: TransportOptions | None,
    warnings: list[str],
) -> dict[str, object]:
    def compact_options(options: list[TransportOption]) -> list[dict]:
        return [
            {
                "departure": option.departure.isoformat(),
                "arrival": option.arrival.isoformat(),
                "duration_minutes": option.duration_minutes,
                "from": option.from_station,
                "to": option.to_station,
                "type": option.transport_type,
                "has_transfers": option.has_transfers,
                "price_rub": option.price_rub,
            }
            for option in options[:3]
        ]

    transport_facts = None
    if transport:
        transport_facts = {
            "outbound": compact_options(transport.outbound),
            "return": compact_options(transport.return_trip),
        }
    return {
        "distance_straight_km": distance_km,
        "origin": origin.title,
        "destination": destination.title,
        "weather": weather.model_dump(mode="json"),
        "transport": transport_facts,
        "warnings": warnings,
    }


async def _with_heartbeat(
    operation: Awaitable[ResultT],
    report: ProgressCallback,
) -> ResultT:
    task = asyncio.ensure_future(operation)
    progress = 68
    try:
        while not task.done():
            done, _ = await asyncio.wait({task}, timeout=3)
            if done:
                break
            next_progress = min(progress + 3, 88)
            if next_progress > progress:
                progress = next_progress
                await report(progress, "ИИ составляет программу и бюджет")
        return await task
    except asyncio.CancelledError:
        task.cancel()
        raise


def _plan_map_url(
    origin: GeoPoint,
    destination: GeoPoint,
    transport: TransportOptions | None,
    *,
    by_car: bool,
) -> str | None:
    if by_car:
        return build_yandex_map_url(origin, destination, by_car=True)
    if transport and transport.outbound:
        return (
            str(transport.outbound[0].map_url)
            if transport.outbound[0].map_url
            else None
        )
    return None


def _share_text(
    *,
    generated: GeneratedTripContent,
    request: TripRequest,
    destination: GeoPoint,
    map_url: str | None,
) -> str:
    date_label = request.start_date.strftime("%d.%m.%Y")
    lines = [
        f"🧭 {generated.title}",
        f"📍 {destination.title} · {date_label} · {request.days} дн.",
        generated.summary,
    ]
    for day in generated.itinerary:
        lines.extend(["", f"{day.date.strftime('%d.%m')} | {day.title}"])
        lines.extend(f"{item.start_time} — {item.title}" for item in day.items)
    if map_url:
        label = (
            "Маршрут на автомобиле" if request.has_car else "Маршрут между станциями"
        )
        lines.extend(["", f"🗺 {label}: {map_url}"])
    return "\n".join(lines)


def _sources(weather: WeatherForecast) -> list[dict[str, str]]:
    return [
        {"name": SOURCE_YANDEX, "url": YANDEX_SCHEDULE_SITE_URL},
        {"name": weather.provider, "url": str(weather.source_url)},
        {"name": "OpenStreetMap Nominatim", "url": NOMINATIM_SITE_URL},
        {"name": "ИИ", "url": GIGACHAT_SITE_URL},
    ]
