"""Diverse suggestions, with relevance taking precedence over novelty."""

import random
import re

from pydantic import BaseModel, Field

from src.errors import ServiceError
from src.models import DestinationSuggestion, OriginCity

DESTINATION_CANDIDATE_COUNT = 5
DESTINATION_SCORE_TOLERANCE = 10
RECENT_DESTINATION_LIMIT = 8
DESTINATION_TEMPERATURE = 0.7

# Exploration hints, not a closed catalog or verified travel/price information.
# See README for regional tourism sources. Geocoding/distance validation remains mandatory.
DESTINATION_HINTS = {
    OriginCity.MOSCOW: (
        "Зарайск", "Дмитров", "Звенигород", "Истра", "Клин", "Серпухов",
        "Можайск", "Волоколамск", "Руза", "Верея", "Талдом", "Дубна",
        "Павловский Посад", "Егорьевск", "Ногинск", "Бронницы", "Чехов",
        "Подольск", "Раменское", "Кашира", "Орехово-Зуево", "Коломна",
        "Сергиев Посад", "Таруса", "Боровск", "Калуга", "Малоярославец",
        "Тула", "Алексин", "Белёв", "Рязань", "Касимов",
        "Владимир", "Суздаль", "Александров", "Юрьев-Польский", "Гороховец",
        "Переславль-Залесский", "Ростов", "Углич", "Мышкин", "Рыбинск",
        "Ярославль", "Тверь", "Торжок", "Старица", "Кимры", "Калязин",
    ),
    OriginCity.SAINT_PETERSBURG: (
        "Гатчина", "Выборг", "Приозерск", "Шлиссельбург", "Тихвин",
        "Волхов", "Новая Ладога", "Луга", "Кингисепп", "Всеволожск",
        "Тосно", "Любань", "Приморск", "Высоцк", "Лодейное Поле",
        "Подпорожье", "Великий Новгород", "Старая Русса", "Валдай",
        "Боровичи", "Псков", "Печоры", "Гдов", "Сортавала", "Лахденпохья",
    ),
}


class DestinationCandidate(DestinationSuggestion):
    fit_score: int = Field(ge=0, le=100, description="Соответствие анкете, не популярность города")


class DestinationCandidates(BaseModel):
    candidates: list[DestinationCandidate] = Field(min_length=1, max_length=DESTINATION_CANDIDATE_COUNT)


def city_key(name: str) -> str:
    value = name.split(",", 1)[0].casefold().replace("ё", "е").strip()
    return re.sub(r"^(?:город\s+|г\.\s*)", "", value)


def choose_destination(candidates: DestinationCandidates, origin: str, recent: list[str]) -> DestinationSuggestion:
    unique = {}
    origin_key = city_key(origin)

    for candidate in candidates.candidates:
        key = city_key(candidate.name)
        if key != origin_key and (key not in unique or candidate.fit_score > unique[key].fit_score):
            unique[key] = candidate

    if not unique:
        raise ServiceError("gigachat", "Не удалось подобрать новое направление. Уточните пожелания.")

    best_score = max(item.fit_score for item in unique.values())
    suitable = [
        item for item in unique.values()
        if item.fit_score >= best_score - DESTINATION_SCORE_TOLERANCE
    ]

    visited = {city_key(name) for name in recent}
    fresh = [item for item in suitable if city_key(item.name) not in visited]

    # A clearly better match wins even when it was visited before.
    selected = random.choice(fresh or suitable)
    return DestinationSuggestion.model_validate(selected.model_dump(exclude={"fit_score"}))
