import httpx
import pytest

from src.models import GeoPoint, TripPlan
from src.sample import sample_trip
from src.services.city_photos import CityPhotoService


@pytest.mark.asyncio
async def test_photo_attribution_cache_and_persistence():
    calls = []

    def respond(request):
        calls.append(request)
        if request.url.host == "ru.wikipedia.org":
            return httpx.Response(
                200,
                json={
                    "query": {
                        "pages": [
                            {
                                "coordinates": [{"lat": 56.86, "lon": 35.9}],
                                "pageimage": "City.jpg",
                                "thumbnail": {
                                    "source": "https://thumb.wikimedia.org/city.jpg"
                                },
                                "fullurl": "https://ru.wikipedia.org/wiki/Тверь",
                            }
                        ]
                    }
                },
            )
        return httpx.Response(
            200,
            json={
                "query": {
                    "pages": [
                        {
                            "imageinfo": [
                                {
                                    "mime": "image/jpeg",
                                    "descriptionurl": "https://commons.wikimedia.org/wiki/File:City.jpg",
                                    "extmetadata": {
                                        "LicenseShortName": {"value": "CC BY-SA 4.0"},
                                        "Artist": {
                                            "value": '<a href="/User:A">Автор</a>'
                                        },
                                    },
                                }
                            ]
                        }
                    ]
                }
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as http:
        service = CityPhotoService(http)
        city = GeoPoint(
            query="Тверь",
            title="Тверь",
            address="Россия",
            latitude=56.86,
            longitude=35.9,
            wikipedia_title="Тверь",
        )
        photo = await service.for_city(city)
        assert photo and photo.author == "Автор"
        assert "license" not in photo.model_dump()
        assert await service.for_city(city) == photo
        assert len(calls) == 2
        plan = sample_trip().model_copy(update={"destination_photo": photo})
        assert (
            TripPlan.model_validate_json(plan.model_dump_json()).destination_photo
            == photo
        )
        # A namesake article at the wrong coordinates is never attached.
        other = city.model_copy(update={"latitude": 43.1, "longitude": 131.8})
        assert await service.for_city(other) is None


@pytest.mark.asyncio
async def test_photo_provider_failure_is_optional():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda r: httpx.Response(503))
    ) as http:
        service = CityPhotoService(http)
        city = GeoPoint(
            query="Тверь",
            title="Тверь",
            address="Россия",
            latitude=56.86,
            longitude=35.9,
            wikipedia_title="Тверь",
        )
        assert await service.for_city(city) is None


@pytest.mark.asyncio
async def test_photo_survives_database_reload(store):
    from src.models import CityPhoto

    plan = sample_trip()
    plan.destination_photo = CityPhoto(
        url="https://thumb.wikimedia.org/city.jpg",
        source_url="https://commons.wikimedia.org/wiki/File:City.jpg",
        article_url="https://ru.wikipedia.org/wiki/Тверь",
        author="Автор",
    )
    await store.put(plan, owner_id="max:42")
    loaded = await store.get(plan.id, owner_id="max:42")
    assert loaded.destination_photo == plan.destination_photo
