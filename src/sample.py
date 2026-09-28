"""Explicit synthetic example for UI review; never a fallback for live providers."""

from datetime import timedelta
from uuid import UUID

from src.models import TripParameters, TripPlan, current_date


def sample_trip() -> TripPlan:
    day = current_date() + timedelta(days=1)
    return TripPlan.model_validate(
        {
            "id": UUID("00000000-0000-4000-8000-000000000001"),
            "request": TripParameters(origin="Москва", destination="Коломна", start_date=day, has_car=True),
            "title": "Коломна: замедлиться на один день",
            "summary": "Старинные улочки, прогулка у кремля и неспешный обед. Пример поездки для двоих: достаточно впечатлений, без гонки за достопримечательностями.",
            "origin": {
                "query": "Москва",
                "title": "Москва",
                "address": "Москва",
                "latitude": 55.75,
                "longitude": 37.61,
                "source": "Демонстрационные данные",
            },
            "destination": {
                "query": "Коломна",
                "title": "Коломна",
                "address": "Коломна",
                "latitude": 55.10,
                "longitude": 38.76,
                "source": "Демонстрационные данные",
            },
            "weather": {
                "provider": "Демо, не прогноз",
                "location": "Коломна",
                "days": [
                    {
                        "date": day,
                        "description": "Переменная облачность · пример",
                        "temperature_min_c": 12,
                        "temperature_max_c": 19,
                        "precipitation_probability_percent": 20,
                    },
                ],
                "source_url": "https://open-meteo.com/",
            },
            "transport": None,
            "itinerary": [
                {
                    "date": day,
                    "title": "Город, который хочется рассмотреть",
                    "items": [
                        {
                            "start_time": "10:30",
                            "end_time": "12:00",
                            "title": "Прогулка у кремля",
                            "place": "Коломенский кремль",
                            "description": "Начните со знакомства с исторической частью города. Оставьте время на фотографии и тихие переулки.",
                            "indoor": False,
                            "estimated_cost_rub": 0,
                        },
                        {
                            "start_time": "12:00",
                            "end_time": "13:00",
                            "title": "Время на местную кухню",
                            "place": "Исторический центр",
                            "description": "Выберите кафе по пути. Стоимость — демонстрационная оценка на всю компанию, столик не забронирован.",
                            "indoor": True,
                            "estimated_cost_rub": 2400,
                        },
                        {
                            "start_time": "13:30",
                            "end_time": "15:00",
                            "title": "История со вкусом пастилы",
                            "place": "Музейная часть города",
                            "description": "Рассмотрите посещение музея пастилы. Сеансы, доступность билетов и цены необходимо проверить самостоятельно.",
                            "indoor": True,
                            "estimated_cost_rub": 1600,
                        },
                        {
                            "start_time": "15:30",
                            "end_time": "17:00",
                            "title": "Ещё немного прогулок",
                            "place": "Старый город",
                            "description": "Пройдитесь по улочкам и сделайте остановку на чай перед возвращением домой.",
                            "indoor": False,
                            "estimated_cost_rub": 600,
                        },
                    ],
                },
            ],
            "budget": {
                "limit_rub": 12000,
                "estimated_total_rub": 7600,
                "per_person_rub": 3800,
                "within_budget": True,
                "items": [
                    {"category": "Дорога на автомобиле", "amount_rub": 3000},
                    {"category": "Еда и чай", "amount_rub": 3000},
                    {"category": "Музей", "amount_rub": 1600},
                ],
            },
            "weather_advice": "В примере пригодится лёгкая куртка. Перед настоящей поездкой запросите актуальный прогноз.",
            "packing_list": [
                "Удобная обувь",
                "Вода",
                "Лёгкая куртка",
                "Зарядка для телефона",
            ],
            "notes": ["Часы работы и билеты в музеи нужно уточнить до поездки."],
            "map_url": "https://yandex.ru/maps/?rtext=55.75,37.61~55.10,38.76&rtt=auto",
            "share_text": "ДЕМО · пример поездки, не актуальный маршрут.\nКоломна: прогулка у кремля, местная кухня и музей пастилы.\nПримерная оценка на двоих: 7 600 ₽. Погоду, цены и часы работы нужно проверить.",
            "warnings": [
                "Это подготовленный пример: погода, программа и стоимость синтетические. Реальные API не вызывались.",
            ],
            "sources": [
                {"name": "Подготовленный пример, без запросов к API", "url": ""},
            ],
        }
    )
