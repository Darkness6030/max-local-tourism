import asyncio
import re
import ssl
import time

import certifi
from geopy.adapters import AioHTTPAdapter
from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from geopy.geocoders import Nominatim

from src.errors import ServiceError
from src.models import GeoPoint


class GeocodingService:
    def __init__(
        self,
        *,
        user_agent: str,
        timeout: float,
        domain: str = "nominatim.openstreetmap.org",
    ) -> None:
        self.domain = domain
        self.user_agent = user_agent
        self.timeout = timeout
        self._lock = asyncio.Lock()
        self._last_request_at = 0.0
        self._cache: dict[str, GeoPoint] = {}

    async def geocode(self, query: str) -> GeoPoint:
        normalized_query = query.strip()
        if not normalized_query:
            raise ServiceError("geocoding", "Пустой поисковый запрос", status_code=422)

        cache_key = normalized_query.casefold()
        if cache_key in self._cache:
            return self._cache[cache_key].model_copy(deep=True)

        async with self._lock:
            if cache_key in self._cache:
                return self._cache[cache_key].model_copy(deep=True)
            wait_seconds = 1.0 - (time.monotonic() - self._last_request_at)
            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)
            try:
                async with Nominatim(
                    user_agent=self.user_agent,
                    domain=self.domain,
                    adapter_factory=AioHTTPAdapter,
                    timeout=self.timeout,
                    ssl_context=ssl.create_default_context(cafile=certifi.where()),
                ) as geocoder:
                    locations = await geocoder.geocode(
                        normalized_query,
                        exactly_one=False,
                        limit=5,
                        language="ru",
                        country_codes="ru",
                        addressdetails=True,
                        namedetails=True,
                        extratags=True,
                        featuretype="settlement",
                    )
            except (GeocoderTimedOut, GeocoderServiceError) as exc:
                raise ServiceError(
                    "geocoding",
                    "Сервис геокодирования временно недоступен",
                    details=str(exc),
                ) from exc
            finally:
                self._last_request_at = time.monotonic()

        locations = [
            location
            for location in (locations or [])
            if _is_matching_city(location, normalized_query)
        ]
        if not locations:
            raise ServiceError(
                "geocoding",
                "Не получилось найти город с таким названием",
                status_code=404,
            )

        # Nominatim часто ставит административную границу Москвы выше городской
        # точки. Для транспорта нужна именно точка населённого пункта.
        location = min(locations, key=_location_rank)
        raw = location.raw or {}
        address_data = raw.get("address") or {}
        title = next(
            (
                address_data.get(key)
                for key in (
                    "city",
                    "town",
                    "village",
                    "municipality",
                    "county",
                    "state",
                )
                if address_data.get(key)
            ),
            str(location.address).split(",", maxsplit=1)[0],
        )

        point = GeoPoint(
            query=normalized_query,
            title=str(title),
            address=str(location.address),
            latitude=float(location.latitude),
            longitude=float(location.longitude),
            wikipedia_title=_wikipedia_title(raw),
        )
        if len(self._cache) >= 512:
            self._cache.pop(next(iter(self._cache)))
        self._cache[cache_key] = point
        return point.model_copy(deep=True)


def _location_rank(location: object) -> tuple[int, int]:
    raw = getattr(location, "raw", {}) or {}
    addresstype = raw.get("addresstype")
    result_class = raw.get("class") or raw.get("category")
    settlement_types = {"city", "town", "village", "hamlet", "municipality", "locality"}
    if result_class == "place" and addresstype in settlement_types:
        return (0, 0)
    if result_class != "boundary":
        return (1, 0)
    return (2, 0)


def _city_name(value: str) -> str:
    value = re.sub(r"^(?:город\s+|г\.\s*)", "", value.strip(), flags=re.IGNORECASE)
    return value.casefold().replace("ё", "е").replace("–", "-").strip()


def _is_matching_city(location: object, query: str) -> bool:
    raw = getattr(location, "raw", {}) or {}
    address = raw.get("address") or {}
    if address.get("country_code") != "ru" or raw.get("addresstype") not in {
        "city",
        "town",
    }:
        return False
    names = [raw.get("name"), address.get("city"), address.get("town")]
    details = raw.get("namedetails") or {}
    for key in (
        "name",
        "name:ru",
        "name:en",
        "official_name",
        "alt_name",
        "short_name",
    ):
        if isinstance(details.get(key), str):
            names.extend(details[key].split(";"))
    sought = _city_name(query.split(",")[0])
    return any(_city_name(name) == sought for name in names if isinstance(name, str))


def _wikipedia_title(raw: dict) -> str | None:
    tag = (raw.get("extratags") or {}).get("wikipedia", "")
    return tag[3:] if isinstance(tag, str) and tag.startswith("ru:") else None
