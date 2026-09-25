import math
from datetime import datetime, timedelta
from urllib.parse import urlencode

from src.constants import DEPARTURE_BUFFER_MINUTES, EARTH_RADIUS_KM, YANDEX_MAPS_URL
from src.models import Coordinates


def build_yandex_map_url(
    origin: Coordinates,
    destination: Coordinates,
    *,
    by_car: bool,
    departure_at: datetime | None = None,
) -> str:
    """Build a route between the exact supplied points, without geocoding them."""
    params = {
        "mode": "routes",
        "rtext": (
            f"{origin.latitude:.6f},{origin.longitude:.6f}~"
            f"{destination.latitude:.6f},{destination.longitude:.6f}"
        ),
        "rtt": "auto" if by_car else "mt",
        "ruri": "~",
    }
    if departure_at is not None:
        map_departure_at = departure_at - timedelta(minutes=DEPARTURE_BUFFER_MINUTES)
        params.update(
            {
                "routes[timeDependent][time]": map_departure_at.replace(
                    tzinfo=None
                ).isoformat(timespec="seconds"),
                "routes[timeDependent][type]": "departure",
            }
        )
    return f"{YANDEX_MAPS_URL}?{urlencode(params)}"


def distance_km(first: Coordinates, second: Coordinates) -> float:
    lat1, lat2 = math.radians(first.latitude), math.radians(second.latitude)
    delta_lat = math.radians(second.latitude - first.latitude)
    delta_lon = math.radians(second.longitude - first.longitude)
    value = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    value = min(1.0, max(0.0, value))
    return EARTH_RADIUS_KM * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))
