import asyncio
from datetime import timedelta
from unittest.mock import AsyncMock

import httpx
import pytest

from src.models import GeoPoint, TripPlan, TripRequest
from src.services.budget import build_budget
from src.services.hotels import HotelCatalog, HotelService
from src.services.planner import TripPlanner
from tests.test_planner import FailingSchedule, FakeAI, FakeGeocoding, FakeWeather


def city():
    return GeoPoint(
        query="Коломна",
        title="Коломна",
        address="Россия",
        latitude=55.09,
        longitude=38.76,
    )


def hotel(node_id=1, **tags):
    return {
        "type": "node",
        "id": node_id,
        "lat": 55.091,
        "lon": 38.761,
        "tags": {
            "tourism": "hotel",
            "name": "Гостиница",
            "website": "https://example.com/",
            **tags,
        },
    }


@pytest.mark.asyncio
async def test_catalog_coordinates_deduplication_links_and_concurrent_cache():
    calls = []

    async def respond(request):
        calls.append(request)
        await asyncio.sleep(0)
        return httpx.Response(
            200,
            json={
                "elements": [
                    hotel(),
                    hotel(2),
                    hotel(3, name="Другой отель", website="javascript:alert(1)"),
                    {**hotel(4), "lat": 10},
                    hotel(5, disused="yes"),
                    {"tags": {}},
                    {
                        "type": "way",
                        "id": 9,
                        "center": {"lat": 55.095, "lon": 38.765},
                        "tags": {
                            "tourism": "guest_house",
                            "name:ru": "Гостевой дом",
                            "addr:street": "Улица",
                            "addr:housenumber": "1",
                        },
                    },
                ]
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as http:
        service = HotelService(http)
        first, second = await asyncio.gather(
            service.for_city(city()), service.for_city(city())
        )
        assert first == second and len(calls) == 1
        assert len(first.hotels) == 3 and first.fetched_at
        assert str(first.hotels[0].website) == "https://example.com/"
        assert first.hotels[1].website is None
        assert first.hotels[2].address == "Улица, 1"
        assert str(first.hotels[2].source_url) == "https://www.openstreetmap.org/way/9"
        assert "38.761" in str(first.hotels[0].map_url)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(429),
        httpx.Response(200, json={"remark": "timeout", "elements": []}),
        httpx.Response(200, json={}),
    ],
)
async def test_unavailable_catalog_has_cooldown_even_for_other_cities(response):
    calls = []

    def respond(request):
        calls.append(request)
        return response

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as http:
        service = HotelService(http)
        assert not (await service.for_city(city())).available
        assert not (
            await service.for_city(city().model_copy(update={"latitude": 56}))
        ).available
        assert len(calls) == 1


@pytest.mark.asyncio
async def test_empty_catalog_is_success_and_cached():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(200, json={"elements": []})
        )
    ) as http:
        service = HotelService(http)
        result = await service.for_city(city())
        assert result.available and not result.hotels
        assert await service.for_city(city()) is result


class MultiDayAI(FakeAI):
    async def build_trip(self, request, **kwargs):
        content = await super().build_trip(request, **kwargs)
        content.itinerary = [
            content.itinerary[0].model_copy(deep=True) for _ in range(request.days)
        ]
        content.lodging_nightly_rub = 6000
        return content


@pytest.mark.asyncio
@pytest.mark.parametrize("days", [1, 2, 3])
async def test_planner_only_loads_hotels_for_overnight_trips(days):
    hotels = AsyncMock()
    hotels.for_city.return_value = HotelCatalog([], available=False)
    planner = TripPlanner(
        geocoding=FakeGeocoding(),
        weather=FakeWeather(),
        schedule=FailingSchedule(),
        ai=MultiDayAI(),
        hotels=hotels,
    )
    request = TripRequest(
        destination="Коломна", days=days, travelers=3, budget_rub=3000
    )
    plan = await planner.generate(request)
    if days == 1:
        hotels.for_city.assert_not_called()
        assert plan.accommodation is None
        assert plan.budget.estimated_total_rub == 2500
    else:
        hotels.for_city.assert_awaited_once()
        assert plan.accommodation.rooms == 2
        assert plan.accommodation.nights == days - 1
        assert plan.accommodation.check_out == request.start_date + timedelta(
            days=days - 1
        )
        assert plan.accommodation.estimated_total_rub == 12000 * (days - 1)
        assert plan.accommodation.status == "unavailable"
        assert not plan.budget.within_budget
        assert plan.budget.estimated_total_rub == (2000 + 12000 * (days - 1)) * 1.25
        assert "запасом" in plan.warnings[-1]
    assert plan.budget.estimated_total_rub == sum(
        item.amount_rub for item in plan.budget.items
    )
    assert TripPlan.model_validate_json(plan.model_dump_json()).model_dump(
        mode="json"
    ) == plan.model_dump(mode="json")


@pytest.mark.asyncio
async def test_no_duplicate_lodging_and_no_mutation():
    from src.models import BudgetItem

    request = TripRequest(destination="Коломна", days=2, budget_rub=10000)
    generated = await MultiDayAI().build_trip(
        request, destination_name="Коломна", facts={}
    )
    generated.budget_items.append(BudgetItem(category="Отель", amount_rub=1000))
    generated.lodging_nightly_rub = None
    budget, stay = build_budget(generated, request, city(), HotelCatalog([]))
    assert stay.estimated_room_night_rub == 5000
    assert stay.status == "empty"
    assert budget.estimated_total_rub == 8750
    assert len(generated.budget_items) == 2
    assert build_budget(generated, request, city(), HotelCatalog([]))[0] == budget


@pytest.mark.asyncio
async def test_hotels_budget_survive_database_reload(store):
    plan = await TripPlanner(
        geocoding=FakeGeocoding(),
        weather=FakeWeather(),
        schedule=FailingSchedule(),
        ai=MultiDayAI(),
    ).generate(TripRequest(destination="Коломна", days=3))
    await store.put(plan, owner_id="max:42")
    restored = await store.get(plan.id, owner_id="max:42")
    assert restored.accommodation == plan.accommodation
    assert restored.budget == plan.budget
    assert (await store.list("max:42")).items[
        0
    ].estimated_total_rub == plan.budget.estimated_total_rub
    assert await store.get(plan.id, owner_id="max:43") is None
