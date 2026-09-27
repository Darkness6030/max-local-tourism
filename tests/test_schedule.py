from datetime import date, time
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from src.models import GeoPoint
from src.services.yandex_schedule import YandexScheduleService


@pytest.mark.asyncio
async def test_yandex_schedule_round_trip_is_normalized() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "secret"
        if request.url.path.endswith("nearest_settlement/"):
            is_origin = float(request.url.params["lng"]) < 38
            return httpx.Response(
                200,
                json={
                    "code": "c213" if is_origin else "c10734",
                    "title": "Москва" if is_origin else "Коломна",
                    "distance": 0.5,
                },
            )
        if request.url.path.endswith("nearest_stations/"):
            assert request.url.params["transport_types"] == "train"
            is_origin = float(request.url.params["lng"]) < 38
            station = (
                {
                    "code": "s2000003",
                    "title": "Москва (Казанский вокзал)",
                    "lat": 55.773678,
                    "lng": 37.658038,
                }
                if is_origin
                else {
                    "code": "s9600716",
                    "title": "Голутвин",
                    "lat": 55.085962,
                    "lng": 38.805724,
                }
            )
            return httpx.Response(200, json={"stations": [station]})
        is_outbound = request.url.params["from"] == "c213"
        departure = (
            "2026-08-22T09:00:00+03:00" if is_outbound else "2026-08-22T18:30:00+03:00"
        )
        arrival = (
            "2026-08-22T11:00:00+03:00" if is_outbound else "2026-08-22T20:30:00+03:00"
        )
        return httpx.Response(
            200,
            json={
                "segments": [
                    {
                        "departure": departure,
                        "arrival": arrival,
                        "duration": 7200,
                        "from": {
                            "code": "s2000003" if is_outbound else "s9600716",
                            "title": (
                                "Москва (Казанский вокзал)"
                                if is_outbound
                                else "Голутвин"
                            ),
                            "transport_type": "train",
                        },
                        "to": {
                            "code": "s9600716" if is_outbound else "s2000003",
                            "title": (
                                "Голутвин"
                                if is_outbound
                                else "Москва (Казанский вокзал)"
                            ),
                            "transport_type": "train",
                        },
                        "thread": {
                            "transport_type": "suburban",
                            "number": "1234",
                            "title": "Москва — Коломна",
                            "carrier": {"title": "ЦППК"},
                        },
                        "tickets_info": {
                            "places": [{"price": {"whole": 450, "cents": 50}}]
                        },
                    }
                ]
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        service = YandexScheduleService(client, api_key="secret")
        result = await service.find_round_trip(
            _point("Москва", 55.75, 37.61),
            _point("Коломна", 55.09, 38.76),
            outbound_date=date(2026, 8, 22),
            return_date=date(2026, 8, 22),
            departure_after=time(8),
            return_after=time(18),
        )

    assert result.origin.code == "c213"
    assert result.outbound[0].price_rub == 450.5
    assert result.outbound[0].duration_minutes == 120
    assert result.return_trip[0].departure.hour == 18
    assert "fromId=c213" in str(result.outbound[0].buy_url)
    assert result.outbound[0].from_station_code == "s2000003"
    assert result.outbound[0].to_station_code == "s9600716"
    assert result.outbound[0].from_station_coordinates is not None
    assert result.outbound[0].from_station_coordinates.latitude == 55.773678
    assert result.outbound[0].to_station_coordinates is not None
    assert result.outbound[0].to_station_coordinates.longitude == 38.805724
    map_query = parse_qs(urlparse(str(result.outbound[0].map_url)).query)
    assert map_query["rtext"] == ["55.773678,37.658038~55.085962,38.805724"]
    assert map_query["rtt"] == ["mt"]
    assert map_query["mode"] == ["routes"]
    assert map_query["ruri"] == ["~"]
    assert map_query["routes[timeDependent][time]"] == ["2026-08-22T08:30:00"]
    assert map_query["routes[timeDependent][type]"] == ["departure"]

    return_map_query = parse_qs(urlparse(str(result.return_trip[0].map_url)).query)
    assert return_map_query["routes[timeDependent][time]"] == ["2026-08-22T18:00:00"]


@pytest.mark.asyncio
async def test_schedule_does_not_fallback_to_city_centers_for_map() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("nearest_settlement/"):
            is_origin = float(request.url.params["lng"]) < 38
            return httpx.Response(
                200,
                json={
                    "code": "c213" if is_origin else "c10734",
                    "title": "Москва" if is_origin else "Коломна",
                },
            )
        if request.url.path.endswith("nearest_stations/"):
            return httpx.Response(200, json={"stations": []})
        return httpx.Response(
            200,
            json={
                "segments": [
                    {
                        "departure": "2026-08-22T09:00:00+03:00",
                        "arrival": "2026-08-22T11:00:00+03:00",
                        "from": {
                            "code": "s2000003",
                            "title": "Москва (Казанский вокзал)",
                            "transport_type": "train",
                        },
                        "to": {
                            "code": "s9600716",
                            "title": "Голутвин",
                            "transport_type": "train",
                        },
                        "thread": {"transport_type": "suburban"},
                    }
                ]
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await YandexScheduleService(client, api_key="secret").find_round_trip(
            _point("Москва", 55.75, 37.61),
            _point("Коломна", 55.09, 38.76),
            outbound_date=date(2026, 8, 22),
            return_date=date(2026, 8, 22),
            departure_after=time(8),
            return_after=time(8),
        )

    assert result.outbound[0].map_url is None
    assert result.outbound[0].from_station_coordinates is None


def _point(title: str, latitude: float, longitude: float) -> GeoPoint:
    return GeoPoint(
        query=title,
        title=title,
        address=f"{title}, Россия",
        latitude=latitude,
        longitude=longitude,
    )


def _segment(kind: str, hour: int, price: float | None) -> dict:
    return {
        "departure": f"2026-08-22T{hour:02}:00:00+03:00",
        "arrival": f"2026-08-22T{hour + 1:02}:00:00+03:00",
        "thread": {"transport_type": kind},
        "tickets_info": {"places": [{"price": {"whole": price}}]},
    }


def _normalize(segments: list[dict], limit: int = 5):
    from src.models import SettlementRef

    return YandexScheduleService(None, api_key=None)._normalize_options(
        {"segments": segments}, after=time(8), travel_date=date(2026, 8, 22),
        origin=SettlementRef(code="c213", title="Москва"),
        destination=SettlementRef(code="c10734", title="Коломна"),
        limit=limit, station_coordinates={},
    )


@pytest.mark.parametrize("cheaper,other", [("suburban", "bus"), ("bus", "suburban")])
def test_mixed_modes_keep_three_cheapest_of_cheaper_type_and_two_of_other(cheaper, other):
    options = _normalize([
        *[_segment(cheaper, hour, price) for hour, price in [(8, 800), (9, 150), (10, 100), (11, 200)]],
        *[_segment(other, hour, price) for hour, price in [(12, 900), (13, 400), (14, 350)]],
        _segment(other, 7, 1),  # Before the requested departure time.
        _segment("plane", 15, 1),
    ])
    assert [option.price_rub for option in options] == [150, 100, 200, 400, 350]
    assert [option.transport_type for option in options].count(cheaper) == 3
    assert [option.transport_type for option in options].count(other) == 2


@pytest.mark.parametrize("kind", ["suburban", "bus", "train"])
def test_single_mode_keeps_first_five_departures_even_when_later_is_cheaper(kind):
    options = _normalize([_segment(kind, hour, 1000 - hour * 10) for hour in range(8, 15)])
    assert [option.departure.hour for option in options] == [8, 9, 10, 11, 12]


def test_unknown_prices_remain_available_but_are_not_treated_as_free():
    options = _normalize([
        *[_segment("suburban", hour, None) for hour in range(8, 12)],
        *[_segment("bus", hour, 100) for hour in range(12, 16)],
    ])
    assert [option.transport_type for option in options] == ["suburban", "suburban", "bus", "bus", "bus"]
    assert options[0].price_rub is None


@pytest.mark.parametrize("train_count,bus_count,expected", [(1, 6, 5), (6, 1, 5), (1, 1, 2)])
def test_short_mode_group_does_not_drop_the_other_mode_or_pad_with_duplicates(train_count, bus_count, expected):
    options = _normalize([
        *[_segment("suburban", 8 + i, 100) for i in range(train_count)],
        *[_segment("bus", 14 + i, 200) for i in range(bus_count)],
    ])
    assert len(options) == expected
    assert {option.transport_type for option in options} == {"suburban", "bus"}
    assert len({(option.transport_type, option.departure) for option in options}) == expected


@pytest.mark.asyncio
async def test_second_mode_on_later_search_page_is_included_in_both_directions():
    offsets = []

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("nearest_settlement/"):
            return httpx.Response(200, json={"code": "c213" if float(request.url.params["lng"]) < 38 else "c10734"})
        offset = int(request.url.params.get("offset", 0))
        offsets.append((request.url.params["from"], offset))
        kind = "suburban" if offset == 0 else "bus"
        return httpx.Response(200, json={
            "pagination": {"total": 8, "limit": 4, "offset": offset},
            "segments": [_segment(kind, 8 + i + offset, 100 + offset * 100) for i in range(4)],
        })

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await YandexScheduleService(client, api_key="secret").find_round_trip(
            _point("Москва", 55.75, 37.61), _point("Коломна", 55.09, 38.76),
            outbound_date=date(2026, 8, 22), return_date=date(2026, 8, 22),
            departure_after=time(8), return_after=time(8),
        )
    assert sorted(offsets) == [("c10734", 0), ("c10734", 4), ("c213", 0), ("c213", 4)]
    for options in (result.outbound, result.return_trip):
        assert [option.transport_type for option in options] == ["suburban"] * 3 + ["bus"] * 2
