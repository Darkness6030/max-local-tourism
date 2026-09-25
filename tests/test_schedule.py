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
