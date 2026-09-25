"""City lead photos from Wikipedia, with Commons attribution and bounded caching."""

import asyncio
import time
from html.parser import HTMLParser
from urllib.parse import urlsplit

import httpx

from src.models import CityPhoto, GeoPoint
from src.routing import distance_km

WIKIPEDIA_API = "https://ru.wikipedia.org/w/api.php"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"


class _PlainText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def plain_text(value: str) -> str:
    parser = _PlainText()
    parser.feed(value)
    return " ".join(" ".join(parser.parts).split())[:500]


def trusted_url(value: str, hosts: set[str]) -> bool:
    parsed = urlsplit(value)
    return parsed.scheme == "https" and parsed.hostname in hosts and not parsed.username


class CityPhotoService:
    def __init__(self, http: httpx.AsyncClient):
        self.http = http
        self._cache: dict[tuple, tuple[float, CityPhoto | None]] = {}
        self._lock = asyncio.Lock()

    async def for_city(self, city: GeoPoint) -> CityPhoto | None:
        key = (city.title, city.latitude, city.longitude)
        cached = self._cache.get(key)
        if cached and cached[0] > time.monotonic():
            return cached[1]
        try:
            async with asyncio.timeout(12):
                async with self._lock:
                    cached = self._cache.get(key)
                    if cached and cached[0] > time.monotonic():
                        return cached[1]
                    photo = await self._find(city)
        except (httpx.HTTPError, TimeoutError, ValueError, KeyError, TypeError):
            photo = None
        if len(self._cache) >= 256:
            self._cache.pop(next(iter(self._cache)))
        self._cache[key] = (time.monotonic() + (86400 if photo else 600), photo)
        return photo

    async def _query(self, url: str, **params) -> dict:
        response = await self.http.get(
            url,
            params={"action": "query", "format": "json", "formatversion": 2, **params},
            timeout=5,
            follow_redirects=False,
        )
        response.raise_for_status()
        return response.json().get("query", {})

    async def _find(self, city: GeoPoint) -> CityPhoto | None:
        # Prefer the OSM article binding. Otherwise find an article by city coordinates,
        # avoiding namesakes and arbitrary first search results.
        title = city.wikipedia_title
        if not title:
            nearby = await self._query(
                WIKIPEDIA_API,
                list="geosearch",
                gscoord=f"{city.latitude}|{city.longitude}",
                gsradius=10000,
                gslimit=50,
            )
            for page in nearby.get("geosearch", []):
                candidate = page.get("title", "")
                if (
                    candidate.casefold() == city.title.casefold()
                    or candidate.casefold().startswith(city.title.casefold() + " (")
                ):
                    title = candidate
                    break
        if not title:
            return None
        result = await self._query(
            WIKIPEDIA_API,
            titles=title,
            redirects=1,
            prop="pageimages|coordinates|info",
            piprop="thumbnail|name",
            pithumbsize=1200,
            pilicense="free",
            inprop="url",
            colimit=1,
        )
        pages = result.get("pages", [])
        if not pages:
            return None
        page = pages[0]
        coordinates = page.get("coordinates") or []
        if not coordinates:
            return None
        # Coordinate match also protects against stale or incorrect OSM tags.

        article_point = city.model_copy(
            update={
                "latitude": coordinates[0]["lat"],
                "longitude": coordinates[0]["lon"],
            }
        )
        if distance_km(city, article_point) > 30:
            return None
        image_url = (page.get("thumbnail") or {}).get("source", "")
        article_url = page.get("fullurl", "")
        filename = page.get("pageimage")
        if (
            not filename
            or not trusted_url(image_url, {"upload.wikimedia.org", "thumb.wikimedia.org"})
            or not trusted_url(article_url, {"ru.wikipedia.org"})
        ):
            return None
        info = await self._query(
            COMMONS_API,
            titles=f"File:{filename}",
            prop="imageinfo",
            iiprop="extmetadata|url|mime",
        )
        image_pages = info.get("pages", [])
        images = image_pages[0].get("imageinfo", []) if image_pages else []
        if not images:
            return None
        image = images[0]
        if image.get("mime") not in {"image/jpeg", "image/png", "image/webp"}:
            return None
        metadata = image.get("extmetadata", {})
        license_name = plain_text(metadata.get("LicenseShortName", {}).get("value", ""))
        if not license_name.lower().startswith(("cc by", "cc0", "public domain")):
            return None
        author = plain_text(metadata.get("Artist", {}).get("value", ""))
        source = image.get("descriptionurl", "")
        if not author or not trusted_url(source, {"commons.wikimedia.org"}):
            return None
        return CityPhoto(
            url=image_url,
            article_url=article_url,
            source_url=source,
            author=author,
            license=license_name,
        )
