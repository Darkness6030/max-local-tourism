from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends

from src.config import Settings, get_settings
from src.models import current_date

router = APIRouter(prefix="/api/v1", tags=["miniapp"])


@router.get("/app-config")
async def app_config(settings: Annotated[Settings, Depends(get_settings)]) -> dict:
    today = current_date()
    horizon = 5 if settings.selected_weather_provider == "openweather" else 16
    return {
        "today": today.isoformat(),
        "last_trip_date": (today + timedelta(days=horizon - 1)).isoformat(),
        "default_date": (today + timedelta(days=1)).isoformat(),
        "max_days": 3,
        "origins": ["Москва", "Санкт-Петербург"],
        "bot_url": f"https://max.ru/{settings.max_bot_username}?startapp"
        if settings.max_bot_username
        else None,
    }
