from __future__ import annotations

import asyncio
from datetime import date, datetime, time
from typing import Any
from urllib.parse import urlencode

import httpx

from src.constants import (
    DEFAULT_TRANSPORT_LIMIT,
    YANDEX_NEAREST_DISTANCE_KM,
    YANDEX_NEAREST_STATIONS_LIMIT,
    YANDEX_SCHEDULE_API_URL,
    YANDEX_SCHEDULE_SITE_URL,
    YANDEX_SEARCH_LIMIT,
)
from src.errors import ServiceError
from src.models import (
    Coordinates,
    GeoPoint,
    SettlementRef,
    TransportOption,
    TransportOptions,
)
from src.routing import build_yandex_map_url


class YandexScheduleService:
    def __init__(self, client: httpx.AsyncClient, *, api_key: str | None) -> None:
        self.client = client
        self.api_key = api_key

    async def find_round_trip(
        self,
        origin: GeoPoint,
        destination: GeoPoint,
        *,
        outbound_date: date,
        return_date: date,
        departure_after: time,
        return_after: time,
        limit: int = DEFAULT_TRANSPORT_LIMIT,
    ) -> TransportOptions:
        if not self.api_key:
            raise ServiceError(
                "yandex_schedule",
                "Не задан YANDEX_SCHEDULE_API_KEY",
                status_code=503,
            )

        origin_settlement, destination_settlement = await self._gather_settlements(
            origin, destination
        )
        outbound_raw, return_raw = await asyncio.gather(
            self._search(
                origin_settlement,
                destination_settlement,
                outbound_date,
            ),
            self._search(
                destination_settlement,
                origin_settlement,
                return_date,
            ),
        )
        station_coordinates = await self._station_coordinates(
            origin,
            destination,
            outbound_raw,
            return_raw,
        )
        return TransportOptions(
            origin=origin_settlement,
            destination=destination_settlement,
            outbound=self._normalize_options(
                outbound_raw,
                after=departure_after,
                origin=origin_settlement,
                destination=destination_settlement,
                travel_date=outbound_date,
                limit=limit,
                station_coordinates=station_coordinates,
            ),
            return_trip=self._normalize_options(
                return_raw,
                after=return_after,
                origin=destination_settlement,
                destination=origin_settlement,
                travel_date=return_date,
                limit=limit,
                station_coordinates=station_coordinates,
            ),
        )

    async def _gather_settlements(
        self, origin: GeoPoint, destination: GeoPoint
    ) -> tuple[SettlementRef, SettlementRef]:
        return await asyncio.gather(
            self._nearest_settlement(origin),
            self._nearest_settlement(destination),
        )

    async def _nearest_settlement(self, point: GeoPoint) -> SettlementRef:
        payload = await self._get_json(
            "/nearest_settlement/",
            params={
                "lat": point.latitude,
                "lng": point.longitude,
                "distance": YANDEX_NEAREST_DISTANCE_KM,
            },
        )
        code = payload.get("code")
        if not code:
            raise ServiceError(
                "yandex_schedule",
                f"Яндекс Расписания не нашёл транспортный город рядом с {point.title}",
                status_code=404,
            )
        return SettlementRef(
            code=code,
            title=payload.get("title") or point.title,
            distance_km=payload.get("distance"),
        )

    async def _search(
        self,
        origin: SettlementRef,
        destination: SettlementRef,
        travel_date: date,
    ) -> dict[str, Any]:
        params = {
            "from": origin.code,
            "to": destination.code,
            "date": travel_date.isoformat(),
            "transfers": "true",
            "limit": YANDEX_SEARCH_LIMIT,
        }
        payload = await self._get_json("/search/", params=params)
        segments = list(payload.get("segments") or [])
        # A second transport type (or its cheapest fare) can be on a later page.
        pagination = payload.get("pagination") or {}
        total = pagination.get("total", len(segments))
        offset = pagination.get("limit") or YANDEX_SEARCH_LIMIT
        while offset < total:
            page = await self._get_json("/search/", params={**params, "offset": offset})
            segments.extend(page.get("segments") or [])
            offset += (page.get("pagination") or {}).get("limit") or YANDEX_SEARCH_LIMIT
        return {**payload, "segments": segments}

    async def _station_coordinates(
        self,
        origin: GeoPoint,
        destination: GeoPoint,
        *payloads: dict[str, Any],
    ) -> dict[str, Coordinates]:
        transport_types = sorted(
            {
                station_type
                for payload in payloads
                for station in _endpoint_stations(payload)
                if (station_type := _station_transport_type(station))
            }
        )
        requests = [
            self._nearest_stations(point, transport_type)
            for point in (origin, destination)
            for transport_type in transport_types
        ]
        responses = await asyncio.gather(*requests, return_exceptions=True)

        result: dict[str, Coordinates] = {}
        for response in responses:
            if isinstance(response, BaseException):
                continue
            for station in response.get("stations") or []:
                code = station.get("code")
                try:
                    coordinates = Coordinates(
                        latitude=station.get("lat"),
                        longitude=station.get("lng"),
                    )
                except (TypeError, ValueError):
                    continue
                if code:
                    result[code] = coordinates
        return result

    async def _nearest_stations(
        self,
        point: GeoPoint,
        transport_type: str,
    ) -> dict[str, Any]:
        return await self._get_json(
            "/nearest_stations/",
            params={
                "lat": point.latitude,
                "lng": point.longitude,
                "distance": YANDEX_NEAREST_DISTANCE_KM,
                "limit": YANDEX_NEAREST_STATIONS_LIMIT,
                "transport_types": transport_type,
            },
        )

    async def _get_json(self, path: str, *, params: dict[str, Any]) -> dict[str, Any]:
        request_params = {
            **params,
            "format": "json",
            "lang": "ru_RU",
        }

        try:
            response = await self.client.get(
                f"{YANDEX_SCHEDULE_API_URL}{path}",
                params=request_params,
                headers={"Authorization": self.api_key or ""},
            )

            response.raise_for_status()
            return response.json()
        except Exception as exc:
            details = str(exc)
            if isinstance(exc, httpx.HTTPStatusError):
                details = exc.response.text[:500]

            raise ServiceError(
                "yandex_schedule",
                "Ошибка запроса к Яндекс Расписаниям",
                details=details,
            ) from exc

    def _normalize_options(
        self,
        payload: dict[str, Any],
        *,
        after: time,
        origin: SettlementRef,
        destination: SettlementRef,
        travel_date: date,
        limit: int,
        station_coordinates: dict[str, Coordinates],
    ) -> list[TransportOption]:
        result: list[TransportOption] = []
        for segment in payload.get("segments") or []:
            departure = _parse_datetime(segment.get("departure"))
            arrival = _parse_datetime(segment.get("arrival"))
            if (
                departure is None
                or arrival is None
                or departure.timetz().replace(tzinfo=None) < after
            ):
                continue

            details = segment.get("details") or []
            thread = (
                segment.get("thread")
                or (details[0].get("thread") if details else {})
                or {}
            )

            from_data = (
                segment.get("from") or (details[0].get("from") if details else {}) or {}
            )

            to_data = (
                segment.get("to") or (details[-1].get("to") if details else {}) or {}
            )

            transport_type = thread.get("transport_type") or "mixed"
            if transport_type in {"plane", "helicopter", "water"}:
                continue

            from_station_code = from_data.get("code")
            to_station_code = to_data.get("code")
            from_coordinates = station_coordinates.get(from_station_code)
            to_coordinates = station_coordinates.get(to_station_code)
            map_url = (
                build_yandex_map_url(
                    from_coordinates,
                    to_coordinates,
                    by_car=False,
                    departure_at=departure,
                )
                if from_coordinates and to_coordinates
                else None
            )

            duration_seconds = int(segment.get("duration") or (arrival - departure).total_seconds())
            result.append(
                TransportOption(
                    departure=departure,
                    arrival=arrival,
                    duration_minutes=max(0, round(duration_seconds / 60)),
                    from_station=from_data.get("title") or origin.title,
                    to_station=to_data.get("title") or destination.title,
                    from_station_code=from_station_code,
                    to_station_code=to_station_code,
                    from_station_coordinates=from_coordinates,
                    to_station_coordinates=to_coordinates,
                    transport_type=transport_type,
                    vehicle=thread.get("vehicle"),
                    route_number=thread.get("number"),
                    route_title=thread.get("title"),
                    carrier=(thread.get("carrier") or {}).get("title"),
                    has_transfers=bool(segment.get("has_transfers") or details),
                    price_rub=_extract_price(segment),
                    buy_url=_buy_url(origin, destination, travel_date),
                    map_url=map_url,
                )
            )

        result.sort(key=lambda option: option.departure)
        return _select_options(result, limit)


def _select_options(options: list[TransportOption], limit: int) -> list[TransportOption]:
    """Keep chronological single-mode results; balance suburban trains and buses."""
    trains = [option for option in options if option.transport_type == "suburban"]
    buses = [option for option in options if option.transport_type == "bus"]
    if not trains or not buses or limit < 2:
        return options[:limit]

    def price_key(option: TransportOption) -> tuple[float, datetime]:
        # Unknown fares are not free: retain them only after known prices.
        return (option.price_rub if option.price_rub is not None else float("inf"), option.departure)

    trains.sort(key=price_key)
    buses.sort(key=price_key)
    primary, secondary = (trains, buses) if price_key(trains[0]) <= price_key(buses[0]) else (buses, trains)
    primary_count = (limit + 1) // 2
    selected = primary[:primary_count] + secondary[:limit - primary_count]
    selected_ids = {id(option) for option in selected}
    remaining = sorted((option for option in options if id(option) not in selected_ids), key=price_key)
    selected.extend(remaining[:limit - len(selected)])
    # The planner uses the first outbound/return option to bound the day's program.
    return sorted(selected, key=lambda option: option.departure)


def _endpoint_stations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    stations: list[dict[str, Any]] = []
    for segment in payload.get("segments") or []:
        details = segment.get("details") or []
        from_data = (
            segment.get("from") or (details[0].get("from") if details else {}) or {}
        )
        to_data = segment.get("to") or (details[-1].get("to") if details else {}) or {}
        stations.extend((from_data, to_data))

    return stations


def _station_transport_type(station: dict[str, Any]) -> str | None:
    transport_type = station.get("transport_type")
    if transport_type == "suburban":
        return "train"
    if transport_type in {"train", "bus"}:
        return transport_type
    return None


def _parse_datetime(value: Any) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _extract_price(segment: dict[str, Any]) -> float | None:
    prices: list[float] = []
    for place in (segment.get("tickets_info") or {}).get("places") or []:
        price = place.get("price") or {}
        if price.get("whole") is not None:
            prices.append(float(price["whole"]) + float(price.get("cents") or 0) / 100)
    return min(prices) if prices else None


def _buy_url(
    origin: SettlementRef, destination: SettlementRef, travel_date: date
) -> str:
    query = urlencode({
        "fromName": origin.title,
        "fromId": origin.code,
        "toName": destination.title,
        "toId": destination.code,
        "when": travel_date.isoformat(),
    })

    return f"{YANDEX_SCHEDULE_SITE_URL}search/?{query}"
