from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx

from src.constants import (
    OPEN_METEO_API_URL,
    OPEN_METEO_SITE_URL,
    OPENWEATHER_API_URL,
    OPENWEATHER_SITE_URL,
)
from src.errors import ServiceError
from src.models import GeoPoint, WeatherDay, WeatherForecast

WMO_DESCRIPTIONS_RU = {
    0: "ясно",
    1: "преимущественно ясно",
    2: "переменная облачность",
    3: "пасмурно",
    45: "туман",
    48: "изморозь и туман",
    51: "слабая морось",
    53: "морось",
    55: "сильная морось",
    56: "слабая ледяная морось",
    57: "ледяная морось",
    61: "слабый дождь",
    63: "дождь",
    65: "сильный дождь",
    66: "слабый ледяной дождь",
    67: "ледяной дождь",
    71: "слабый снег",
    73: "снег",
    75: "сильный снег",
    77: "снежная крупа",
    80: "слабые ливни",
    81: "ливни",
    82: "сильные ливни",
    85: "слабый снегопад",
    86: "сильный снегопад",
    95: "гроза",
    96: "гроза с небольшим градом",
    99: "гроза с сильным градом",
}


class WeatherService:
    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        provider: str,
        openweather_api_key: str | None = None,
    ) -> None:
        self.client = client
        self.provider = provider
        self.openweather_api_key = openweather_api_key

    async def forecast(
        self,
        point: GeoPoint,
        start_date: date,
        days: int,
    ) -> WeatherForecast:
        if self.provider == "openweather":
            if not self.openweather_api_key:
                raise ServiceError(
                    "weather",
                    "Для OpenWeatherMap не задан OPENWEATHER_API_KEY",
                    status_code=503,
                )
            return await self._openweather(point, start_date, days)
        return await self._open_meteo(point, start_date, days)

    async def _open_meteo(
        self,
        point: GeoPoint,
        start_date: date,
        days: int,
    ) -> WeatherForecast:
        end_date = start_date + timedelta(days=days - 1)
        params = {
            "latitude": point.latitude,
            "longitude": point.longitude,
            "daily": (
                "weather_code,temperature_2m_max,temperature_2m_min,"
                "precipitation_probability_max,precipitation_sum,wind_speed_10m_max"
            ),
            "wind_speed_unit": "ms",
            "timezone": "auto",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
        payload = await self._get_json(
            OPEN_METEO_API_URL, params=params, service_name="Open-Meteo"
        )
        daily = payload.get("daily") or {}
        dates = daily.get("time") or []
        result: list[WeatherDay] = []
        for index, raw_date in enumerate(dates):
            code = _list_value(daily, "weather_code", index, 3)
            result.append(
                WeatherDay(
                    date=date.fromisoformat(raw_date),
                    description=WMO_DESCRIPTIONS_RU.get(
                        int(code), "погодные условия без описания"
                    ),
                    temperature_min_c=round(
                        float(_list_value(daily, "temperature_2m_min", index, 0)), 1
                    ),
                    temperature_max_c=round(
                        float(_list_value(daily, "temperature_2m_max", index, 0)), 1
                    ),
                    precipitation_probability_percent=_optional_int(
                        _list_value(daily, "precipitation_probability_max", index)
                    ),
                    precipitation_mm=_optional_float(
                        _list_value(daily, "precipitation_sum", index)
                    ),
                    wind_max_ms=_optional_float(
                        _list_value(daily, "wind_speed_10m_max", index)
                    ),
                )
            )
        if len(result) != days:
            raise ServiceError(
                "weather", "Прогноз Open-Meteo не содержит все даты поездки"
            )
        return WeatherForecast(
            provider="Open-Meteo",
            location=point.title,
            timezone=payload.get("timezone"),
            days=result,
            source_url=OPEN_METEO_SITE_URL,
        )

    async def _openweather(
        self,
        point: GeoPoint,
        start_date: date,
        days: int,
    ) -> WeatherForecast:
        params = {
            "lat": point.latitude,
            "lon": point.longitude,
            "appid": self.openweather_api_key,
            "units": "metric",
            "lang": "ru",
        }
        payload = await self._get_json(
            OPENWEATHER_API_URL, params=params, service_name="OpenWeatherMap"
        )
        timezone_offset = int((payload.get("city") or {}).get("timezone") or 0)
        by_day: dict[date, list[dict[str, Any]]] = defaultdict(list)
        for entry in payload.get("list") or []:
            timestamp = int(entry.get("dt") or 0) + timezone_offset
            local_day = datetime.fromtimestamp(timestamp, timezone.utc).date()
            by_day[local_day].append(entry)

        result: list[WeatherDay] = []
        for offset in range(days):
            target = start_date + timedelta(days=offset)
            entries = by_day.get(target, [])
            if not entries:
                raise ServiceError(
                    "weather",
                    f"OpenWeatherMap не вернул прогноз на {target.isoformat()}",
                    status_code=422,
                )
            descriptions = [
                (item.get("weather") or [{}])[0].get("description", "без описания")
                for item in entries
            ]
            temperatures = [
                float((item.get("main") or {}).get("temp", 0)) for item in entries
            ]
            rain = sum(float((item.get("rain") or {}).get("3h", 0)) for item in entries)
            snow = sum(float((item.get("snow") or {}).get("3h", 0)) for item in entries)
            result.append(
                WeatherDay(
                    date=target,
                    description=Counter(descriptions).most_common(1)[0][0],
                    temperature_min_c=round(min(temperatures), 1),
                    temperature_max_c=round(max(temperatures), 1),
                    precipitation_probability_percent=round(
                        max(float(item.get("pop") or 0) for item in entries) * 100
                    ),
                    precipitation_mm=round(rain + snow, 1),
                    wind_max_ms=round(
                        max(
                            float((item.get("wind") or {}).get("speed", 0))
                            for item in entries
                        ),
                        1,
                    ),
                )
            )
        return WeatherForecast(
            provider="OpenWeatherMap",
            location=point.title,
            timezone=f"UTC{timezone_offset / 3600:+g}",
            days=result,
            source_url=OPENWEATHER_SITE_URL,
        )

    async def _get_json(
        self,
        url: str,
        *,
        params: dict[str, Any],
        service_name: str,
    ) -> dict[str, Any]:
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            details = str(exc)
            if isinstance(exc, httpx.HTTPStatusError):
                details = exc.response.text[:500]
            raise ServiceError(
                "weather",
                f"Не удалось получить прогноз {service_name}",
                details=details,
            ) from exc


def _list_value(data: dict[str, Any], key: str, index: int, default: Any = None) -> Any:
    values = data.get(key) or []
    return values[index] if index < len(values) else default


def _optional_float(value: Any) -> float | None:
    return None if value is None else round(float(value), 1)


def _optional_int(value: Any) -> int | None:
    return None if value is None else round(float(value))
