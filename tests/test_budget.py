from datetime import datetime, timedelta, timezone

import pytest

from src.models import (
    BudgetItem,
    SettlementRef,
    TransportOption,
    TransportOptions,
    TripRequest,
)
from src.services.budget import build_budget
from tests.test_planner import FakeAI, FakeGeocoding


def schedule(outbound, inbound):
    def option(price):
        now = datetime.now(timezone.utc)
        return TransportOption(departure=now, arrival=now + timedelta(hours=1), duration_minutes=60,
                               from_station="Москва", to_station="Коломна", transport_type="bus",
                               price_rub=price, buy_url="https://rasp.yandex.ru/")
    return TransportOptions(origin=SettlementRef(code="c213", title="Москва"),
                            destination=SettlementRef(code="c10734", title="Коломна"),
                            outbound=[option(outbound)], return_trip=[option(inbound)])


@pytest.mark.asyncio
@pytest.mark.parametrize("outbound,inbound,estimate_out,estimate_back,expected,estimated", [
    (450, 520, 100, 100, 2910, False),
    (450, None, None, None, 2700, True),
    (None, 520, None, None, 3120, True),
    (None, None, 400, 500, 2700, True),
    (450, None, 400, 500, 2850, True),
    (0, 0, 400, 500, 0, False),
])
async def test_round_trip_fares_for_entire_group(outbound, inbound, estimate_out, estimate_back, expected, estimated):
    request = TripRequest(destination="Коломна", travelers=3)
    generated = await FakeAI().build_trip(request, destination_name="Коломна", facts={})
    generated.outbound_fare_rub, generated.return_fare_rub = estimate_out, estimate_back
    generated.budget_items += [BudgetItem(category="Транспорт туда-обратно", amount_rub=400),
                              BudgetItem(category="Местный транспорт", amount_rub=200),
                              BudgetItem(category="Входные билеты в музей", amount_rub=600)]
    original = generated.model_dump()
    budget, _ = build_budget(generated, request, await FakeGeocoding().geocode("Коломна"), None, schedule(outbound, inbound))
    fare, = [item for item in budget.items if item.category == "intercity_transport"]
    assert fare.amount_rub == expected
    assert "× 3 чел." in fare.comment
    assert ("оценка" in fare.comment) is estimated
    assert budget.estimated_total_rub == (2000 + 200 + 600 + expected) * 1.2
    assert generated.model_dump() == original


@pytest.mark.asyncio
async def test_unknown_fares_are_explicit_and_car_cost_is_untouched():
    request = TripRequest(destination="Коломна")
    generated = await FakeAI().build_trip(request, destination_name="Коломна", facts={})
    destination = await FakeGeocoding().geocode("Коломна")
    budget, _ = build_budget(generated, request, destination, None)
    fare = next(item for item in budget.items if item.category == "intercity_transport")
    assert fare.amount_rub == 0
    assert "не включена в итог" in fare.comment
    generated.budget_items.append(BudgetItem(category="Дорога на автомобиле", amount_rub=1200))
    request.has_car = True
    budget, _ = build_budget(generated, request, destination, None, schedule(450, 520))
    assert not any(item.category == "intercity_transport" for item in budget.items)
    assert budget.estimated_total_rub == 3840
