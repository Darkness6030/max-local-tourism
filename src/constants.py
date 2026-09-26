"""Общие ограничения и адреса внешних сервисов."""

from zoneinfo import ZoneInfo

MSK_TIMEZONE = ZoneInfo("Europe/Moscow")

MAX_FORECAST_DAYS = 16
MAX_TRIP_DAYS = 3
DEFAULT_TRANSPORT_LIMIT = 5
YANDEX_SEARCH_LIMIT = 100
YANDEX_NEAREST_DISTANCE_KM = 50
YANDEX_NEAREST_STATIONS_LIMIT = 50
ESTIMATED_REGIONAL_SPEED_KMH = 50

YANDEX_SCHEDULE_API_URL = "https://api.rasp.yandex-net.ru/v3.0"
YANDEX_SCHEDULE_SITE_URL = "https://rasp.yandex.ru/"
YANDEX_MAPS_URL = "https://yandex.ru/maps/"
OPEN_METEO_API_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_SITE_URL = "https://open-meteo.com/"
OPENWEATHER_API_URL = "https://api.openweathermap.org/data/2.5/forecast"
OPENWEATHER_SITE_URL = "https://openweathermap.org/"
NOMINATIM_SITE_URL = "https://nominatim.openstreetmap.org/"
GIGACHAT_SITE_URL = "https://developers.sber.ru/portal/products/gigachat-api"

SOURCE_YANDEX = "Яндекс Расписания"
SOURCE_NOMINATIM = "OpenStreetMap Nominatim via geopy"

# Product rules shared by validation, routing and estimates.
MIN_CITY_DISTANCE_KM = 5
MAX_CITY_DISTANCE_KM = 600
SUGGESTED_CITY_DISTANCE_KM = 500
EARTH_RADIUS_KM = 6371.0
DEPARTURE_BUFFER_MINUTES = 30
BUDGET_RESERVE_PERCENT = 20
DEFAULT_ROOM_NIGHT_RUB = 5000  # Planning assumption, not a hotel tariff.
TRAVELERS_PER_ROOM = 2
OVERPASS_API_URL = "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
OSM_COPYRIGHT_URL = "https://www.openstreetmap.org/copyright"
