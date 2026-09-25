from datetime import date, datetime, time, timedelta

import pytest

from src.errors import ServiceError
from src.models import (
    BudgetItem,
    Coordinates,
    GeneratedTripContent,
    GeoPoint,
    ItineraryDay,
    SettlementRef,
    TimelineItem,
    TransportOption,
    TransportOptions,
    TripRequest,
    WeatherDay,
    WeatherForecast,
    current_date,
)
from src.routing import build_yandex_map_url
from src.services.planner import TripPlanner


class FakeGeocoding:
    async def geocode(self, query: str) -> GeoPoint:
        is_moscow = "Москва" in query
        return GeoPoint(
            query=query,
            title="Москва" if is_moscow else "Коломна",
            address=query,
            latitude=55.75 if is_moscow else 55.09,
            longitude=37.61 if is_moscow else 38.76,
        )


class FakeWeather:
    async def forecast(
        self, point: GeoPoint, start_date: date, days: int
    ) -> WeatherForecast:
        return WeatherForecast(
            provider="Open-Meteo",
            location=point.title,
            days=[
                WeatherDay(
                    date=start_date,
                    description="ясно",
                    temperature_min_c=12,
                    temperature_max_c=22,
                )
            ],
            source_url="https://open-meteo.com/",
        )


class FailingSchedule:
    async def find_round_trip(self, *args, **kwargs):
        raise ServiceError("yandex_schedule", "временная ошибка")


class StationSchedule:
    async def find_round_trip(self, *args, **kwargs) -> TransportOptions:
        travel_date = kwargs["outbound_date"]
        origin_coordinates = Coordinates(latitude=55.773678, longitude=37.658038)
        destination_coordinates = Coordinates(
            latitude=55.085962,
            longitude=38.805724,
        )
        option = TransportOption(
            departure=datetime.combine(travel_date, time(9)),
            arrival=datetime.combine(travel_date, time(11)),
            duration_minutes=120,
            from_station="Москва (Казанский вокзал)",
            to_station="Голутвин",
            from_station_code="s2000003",
            to_station_code="s9600716",
            from_station_coordinates=origin_coordinates,
            to_station_coordinates=destination_coordinates,
            transport_type="suburban",
            buy_url="https://rasp.yandex.ru/search/",
            map_url=build_yandex_map_url(
                origin_coordinates,
                destination_coordinates,
                by_car=False,
                departure_at=datetime.combine(travel_date, time(9)),
            ),
        )
        return TransportOptions(
            origin=SettlementRef(code="c213", title="Москва"),
            destination=SettlementRef(code="c10734", title="Коломна"),
            outbound=[option],
            return_trip=[],
        )


class FakeAI:
    async def build_trip(
        self, request, *, destination_name, facts
    ) -> GeneratedTripContent:
        return GeneratedTripContent(
            title="Выходной в Коломне",
            summary="Готовый спокойный маршрут с историей и местной кухней.",
            itinerary=[
                ItineraryDay(
                    date=request.start_date,
                    title="Знакомство с городом",
                    items=[
                        TimelineItem(
                            start_time="10:00:00",
                            end_time="12:00:00",
                            title="Исторический центр",
                            place="Коломенский кремль",
                            description="Прогулка по историческому центру города.",
                            indoor=False,
                        ),
                        TimelineItem(
                            start_time="12:30:00",
                            end_time="14:00:00",
                            title="Обед",
                            place="Центр Коломны",
                            description="Обед с блюдами местной кухни.",
                            indoor=True,
                            estimated_cost_rub=2000,
                        ),
                    ],
                )
            ],
            budget_items=[BudgetItem(category="Еда", amount_rub=2000)],
            weather_advice="Погода подходит для длительной прогулки.",
            packing_list=["Вода", "Удобная обувь"],
        )


@pytest.mark.asyncio
async def test_planner_reports_progress_and_tolerates_schedule_error() -> None:
    planner = TripPlanner(
        geocoding=FakeGeocoding(),
        weather=FakeWeather(),
        schedule=FailingSchedule(),
        gigachat=FakeAI(),
    )
    request = TripRequest(
        origin="Москва",
        destination="Коломна",
        start_date=current_date() + timedelta(days=2),
        budget_rub=5000,
    )
    progress: list[int] = []

    async def report(value: int, _: str) -> None:
        progress.append(value)

    result = await planner.generate(request, progress=report)

    assert result.transport is None
    assert result.budget.within_budget is True
    assert "Транспорт не загружен" in result.warnings[0]
    assert result.itinerary[0].items[0].start_time == "10:00"
    assert progress == sorted(progress)
    assert progress[-1] == 100


@pytest.mark.asyncio
async def test_planner_uses_first_trip_station_coordinates_for_map() -> None:
    planner = TripPlanner(
        geocoding=FakeGeocoding(),
        weather=FakeWeather(),
        schedule=StationSchedule(),
        gigachat=FakeAI(),
    )
    request = TripRequest(
        origin="Москва",
        destination="Коломна",
        start_date=current_date() + timedelta(days=2),
        budget_rub=5000,
    )

    result = await planner.generate(request)

    assert result.transport is not None
    assert result.map_url == result.transport.outbound[0].map_url
    assert "55.773678" in str(result.map_url)
    assert "55.750000" not in str(result.map_url)
    assert "Маршрут между станциями" in result.share_text
