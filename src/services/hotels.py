"""Small, cached Overpass queries; catalog data, never room inventory or rates."""

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlencode, urlsplit

import httpx
from pydantic import ValidationError

from src.constants import OVERPASS_API_URL, YANDEX_MAPS_URL
from src.models import Coordinates, GeoPoint, Hotel
from src.routing import distance_km

HOTEL_RADIUS_METERS = 8000
HOTEL_LIMIT = 5
CATALOG_CACHE_SECONDS = 86400
FAILURE_CACHE_SECONDS = 300
CATALOG_CACHE_SIZE = 256
HOTEL_TIMEOUT_SECONDS = 40


@dataclass(frozen=True)
class HotelCatalog:
    hotels: list[Hotel]
    available: bool = True
    fetched_at: datetime | None = None


def hotel_search_url(city: GeoPoint) -> str:
    return f"{YANDEX_MAPS_URL}?{urlencode({'text': f'Гостиницы {city.title}', 'll': f'{city.longitude},{city.latitude}', 'z': 13})}"


class HotelService:
    def __init__(self, http: httpx.AsyncClient, endpoint: str = OVERPASS_API_URL):
        self.http = http
        self.endpoint = endpoint
        self._cache: dict[tuple, tuple[float, HotelCatalog]] = {}
        self._lock = asyncio.Lock()
        self._retry_after = 0.0

    async def for_city(self, city: GeoPoint) -> HotelCatalog:
        key = (city.latitude, city.longitude)
        cached = self._cached(key)
        if cached is not None:
            return cached
        try:
            async with asyncio.timeout(HOTEL_TIMEOUT_SECONDS):
                async with self._lock:
                    cached = self._cached(key)
                    if cached is not None:
                        return cached
                    if time.monotonic() < self._retry_after:
                        return HotelCatalog([], available=False)
                    result = await self._fetch(city)
                    if len(self._cache) >= CATALOG_CACHE_SIZE:
                        self._cache.pop(next(iter(self._cache)))
                    self._cache[key] = (
                        time.monotonic() + CATALOG_CACHE_SECONDS,
                        result,
                    )
                    return result
        except (httpx.HTTPError, TimeoutError, ValueError, TypeError, KeyError):
            # A provider failure must not fail the itinerary or trigger a request storm.
            self._retry_after = time.monotonic() + FAILURE_CACHE_SECONDS
            return HotelCatalog([], available=False)

    def _cached(self, key: tuple) -> HotelCatalog | None:
        cached = self._cache.get(key)
        return cached[1] if cached and cached[0] > time.monotonic() else None

    async def _fetch(self, city: GeoPoint) -> HotelCatalog:
        query = (
            "[out:json][timeout:10][maxsize:16777216];"
            'nwr["tourism"~"^(hotel|guest_house)$"]'
            f"(around:{HOTEL_RADIUS_METERS},{city.latitude},{city.longitude});"
            "out center tags 100;"
        )

        response = await self.http.post(
            self.endpoint,
            data={"data": query},
            timeout=HOTEL_TIMEOUT_SECONDS,
            follow_redirects=False,
        )

        response.raise_for_status()
        payload = response.json()
        if payload.get("remark") or not isinstance(payload.get("elements"), list):
            raise ValueError("Incomplete Overpass response")

        hotels = []
        for element in payload["elements"]:
            try:
                hotel = _parse_hotel(element, city)
            except (ValidationError, ValueError, TypeError, KeyError):
                continue

            if hotel:
                hotels.append(hotel)

        hotels.sort(key=lambda hotel: hotel.distance_km)
        unique: list[Hotel] = []
        for hotel in hotels:
            if any(
                hotel.name.casefold() == other.name.casefold()
                and distance_km(hotel, other) < 0.2
                for other in unique
            ):
                continue

            unique.append(hotel)
            if len(unique) == HOTEL_LIMIT:
                break

        return HotelCatalog(unique, fetched_at=datetime.now(timezone.utc))


def _parse_hotel(element: dict, city: GeoPoint) -> Hotel | None:
    tags = element.get("tags", {})
    name = tags.get("name:ru") or tags.get("name")
    if not name or tags.get("tourism") not in {"hotel", "guest_house"}:
        return None

    if any(tags.get(key) == "yes" for key in ("disused", "abandoned", "demolished")):
        return None

    element_type, element_id = element["type"], element["id"]
    if element_type not in {"node", "way", "relation"} or type(element_id) is not int:
        return None

    point = element.get("center") or element
    coordinates = Coordinates(latitude=point["lat"], longitude=point["lon"])
    distance = distance_km(city, coordinates)
    if distance * 1000 > HOTEL_RADIUS_METERS:
        return None

    address = ", ".join(
        str(tags[key]) for key in ("addr:street", "addr:housenumber") if tags.get(key)
    ) or tags.get("addr:full")

    website = tags.get("website") or tags.get("contact:website")
    if website:
        parsed = urlsplit(website)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
        ):
            website = None

    map_query = urlencode({"pt": f"{coordinates.longitude},{coordinates.latitude},pm2blm", "z": 16})
    return Hotel(
        id=f"{element_type}/{element_id}",
        name=name,
        kind=tags["tourism"],
        **coordinates.model_dump(),
        address=address,
        distance_km=round(distance, 1),
        website=website,
        map_url=f"{YANDEX_MAPS_URL}?{map_query}",
        source_url=f"https://www.openstreetmap.org/{element_type}/{element_id}",
    )
