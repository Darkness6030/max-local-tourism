from dataclasses import dataclass

import httpx
from pydantic import SecretStr

from src.config import Settings
from src.database import Database
from src.jobs import TripJobManager
from src.services.city_photos import CityPhotoService
from src.services.geocoding import GeocodingService
from src.services.gigachat_ai import GigaChatService
from src.services.hotels import HotelService
from src.services.planner import TripPlanner
from src.services.weather import WeatherService
from src.services.yandex_schedule import YandexScheduleService
from src.store import TripStore


@dataclass
class Container:
    database: Database
    http: httpx.AsyncClient
    geocoding: GeocodingService
    weather: WeatherService
    schedule: YandexScheduleService
    ai: GigaChatService
    store: TripStore
    planner: TripPlanner
    jobs: TripJobManager

    @classmethod
    def build(cls, settings: Settings) -> "Container":
        if not settings.database_url:
            raise ValueError("Задайте DATABASE_URL для постоянного хранения поездок")
        database = Database(settings.database_url.get_secret_value())
        http = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.http_timeout_seconds),
            headers={"User-Agent": settings.nominatim_user_agent},
            follow_redirects=True,
        )
        geocoding = GeocodingService(
            user_agent=settings.nominatim_user_agent,
            domain=settings.nominatim_domain,
            timeout=settings.http_timeout_seconds,
        )
        weather = WeatherService(
            http,
            provider=settings.selected_weather_provider,
            openweather_api_key=_secret_value(settings.openweather_api_key),
        )
        schedule = YandexScheduleService(
            http,
            api_key=_secret_value(settings.yandex_schedule_api_key),
        )
        ai = GigaChatService(
            credentials=_secret_value(settings.gigachat_credentials),
            scope=settings.gigachat_scope,
            model=settings.gigachat_model,
            verify_ssl_certs=settings.gigachat_verify_ssl_certs,
            ca_bundle_file=settings.gigachat_ca_bundle_file,
            timeout=settings.gigachat_timeout_seconds,
        )
        store = TripStore(database.sessions)
        planner = TripPlanner(
            geocoding=geocoding,
            weather=weather,
            schedule=schedule,
            ai=ai,
            photos=CityPhotoService(http),
            hotels=HotelService(http, endpoint=str(settings.overpass_api_url)),
        )
        jobs = TripJobManager(planner, store, max_active=settings.max_job_concurrency)
        return cls(
            database=database,
            http=http,
            geocoding=geocoding,
            weather=weather,
            schedule=schedule,
            ai=ai,
            store=store,
            planner=planner,
            jobs=jobs,
        )

    async def start(self) -> None:
        await self.database.initialize()
        await self.database.acquire_worker()
        await self.store.recover_interrupted_jobs()

    async def close(self) -> None:
        await self.jobs.close()
        await self.ai.close()
        await self.http.aclose()
        await self.database.close()


def _secret_value(secret: SecretStr | None) -> str | None:
    return secret.get_secret_value() if secret else None
