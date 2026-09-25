from __future__ import annotations

import json
import random
import re
from typing import TypeVar

from gigachat import GigaChat
from pydantic import BaseModel

from src.constants import BUDGET_RESERVE_PERCENT, SUGGESTED_CITY_DISTANCE_KM
from src.errors import ServiceError
from src.models import (
    DestinationSuggestion,
    GeneratedTripContent,
    TripRequest,
)
from src.services.destinations import (
    DESTINATION_CANDIDATE_COUNT,
    DESTINATION_HINTS,
    DESTINATION_TEMPERATURE,
    DestinationCandidates,
    choose_destination,
)

ModelT = TypeVar("ModelT", bound=BaseModel)


class GigaChatService:
    def __init__(
        self,
        *,
        credentials: str | None,
        scope: str,
        model: str,
        verify_ssl_certs: bool,
        ca_bundle_file: str | None,
        timeout: float,
    ) -> None:
        self._client = (
            GigaChat(
                credentials=credentials,
                scope=scope,
                model=model,
                verify_ssl_certs=verify_ssl_certs,
                ca_bundle_file=ca_bundle_file or None,
                timeout=timeout,
                max_retries=1,
            )
            if credentials
            else None
        )

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()

    async def suggest_destination(
        self, request: TripRequest, recent_destinations: list[str] | None = None
    ) -> DestinationSuggestion:
        recent = recent_destinations or []
        hints = list(DESTINATION_HINTS[request.origin])
        random.shuffle(hints)
        prompt = f"""
Сравни направления и предложи до {DESTINATION_CANDIDATE_COUNT} РАЗНЫХ реальных городов
России для этой анкеты. Сначала оцени интересы, затем длительность, дорогу,
автомобиль, бюджет на человека, состав группы, возраст детей, темп и сезон.
fit_score (0–100) оценивает соответствие именно этой анкете, а не известность города.
90–100: полностью закрывает главный интерес и ограничения; 70–89: есть компромисс;
ниже 70: лишь общее сходство. Если главный интерес не представлен, оценка не выше 60.
Если интерес конкретный (композитор, космонавтика, живопись), в reason назови
реального известного представителя или профильный музей. Обычный краеведческий
музей не заменяет профильный интерес. Не включай город, если не уверен в фактах.
В reason конкретно объясни связь города с пожеланиями; не используй одинаковые
объяснения для разных городов. Не придумывай достопримечательности и возможности.

АНКЕТА:
{request.model_dump_json(indent=2)}

Города для расширения поиска (порядок случайный, список НЕ исчерпывающий):
{json.dumps(hints, ensure_ascii=False)}
Можно предлагать другие, в том числе менее известные города, если они подходят лучше.
Не выбирай Коломну или Сергиев Посад по привычке: у них нет приоритета.
Подбери несколько сопоставимо хороших вариантов. Если запрос узкий и подходят
только 1–2 города, верни их; не дополняй список неподходящими ради количества.
Города, уже встречавшиеся в последних поездках пользователя:
{json.dumps(recent, ensure_ascii=False)}
Предпочитай новые сопоставимые варианты, но не жертвуй главным пожеланием ради новизны.

Ограничения: каждый город менее чем в {SUGGESTED_CITY_DISTANCE_KM} км по прямой от
{request.origin.value}; сам город отправления исключён. Дорога в одну сторону
примерно не более {request.max_travel_minutes} минут, с учётом наличия автомобиля.
Для одного дня не предлагай дальние города, где дорога съест весь день.
Не предлагай закрытые города или места с обязательными пропусками.
Регион — субъект РФ; названия должны однозначно находиться русским геокодером.
Не выдумывай точные расписания и цены: они проверяются отдельно.
""".strip()
        candidates = await self._structured(
            DestinationCandidates,
            system="Ты — эксперт по локальному туризму России. Сравнивай соответствие запросу, а не популярность.",
            prompt=prompt,
            max_tokens=2000,
            temperature=DESTINATION_TEMPERATURE,
        )
        return choose_destination(candidates, request.origin.value, recent)

    async def build_trip(
        self,
        request: TripRequest,
        *,
        destination_name: str,
        facts: dict,
    ) -> GeneratedTripContent:
        prompt = f"""
Составь готовый сценарий поездки в {destination_name} по анкете пользователя.

АНКЕТА:
{request.model_dump_json(indent=2)}

ПРОВЕРЕННЫЕ BACKEND-ФАКТЫ (единственный источник погоды и транспорта):
{json.dumps(facts, ensure_ascii=False, indent=2, default=str)}

Правила:
- программа ровно на {request.days} дн., даты — начиная с {request.start_date};
- учитывай реальную погоду и время доступных рейсов; если рейсов нет, не выдумывай их;
- itinerary содержит только активности в месте назначения, без междугородних переездов:
  время транспорта показывается отдельно из API, не пересказывай его в программе;
- если пользователь без автомобиля и рейсы найдены, ориентируйся на первый рейс
  туда и первый рейс обратно: начинай активности после прибытия плюс 30 минут,
  заканчивай не позднее отправления обратно минус 30 минут;
- не придумывай точные цены, часы работы, адреса и URL; оценки помечай как оценки;
- budget_items — реалистичные базовые расходы на всю группу за все дни, без проживания
  и без резерва. Учитывай питание, дорогу в обе стороны, местный транспорт и активности;
- лимит {request.budget_rub} рублей — пожелание, не повод занижать цены. Если его не хватает,
  честно оцени необходимые расходы; backend отдельно добавит запас {BUDGET_RESERVE_PERCENT}%;
- estimated_cost_rub активностей — базовая оценка на всю группу, уже включённая в budget_items;
- для поездки длиннее одного дня в lodging_nightly_rub укажи реалистичную оценку
  одного двухместного номера за одну ночь в этом городе на даты поездки.
  Не приписывай эту оценку конкретной гостинице; для одного дня верни null;
- не рекомендуй гостиницы по памяти: отдельный блок реальных гостиниц добавляет backend;
- добавь запас времени до отправления и практичные советы;
- время в timeline указывай в формате HH:MM без секунд;
- пиши по-русски, конкретно и компактно.
""".strip()
        return await self._structured(
            GeneratedTripContent,
            system=(
                "Ты — планировщик поездок выходного дня. Строго опирайся на переданные "
                "данные API и возвращай структурированный результат."
            ),
            prompt=prompt,
            max_tokens=min(3800, 1600 + request.days * 700),
        )

    async def _structured(
        self,
        response_model: type[ModelT],
        *,
        system: str,
        prompt: str,
        max_tokens: int,
        temperature: float = 0.2,
    ) -> ModelT:
        if self._client is None:
            raise ServiceError(
                "gigachat", "Не задан GIGACHAT_CREDENTIALS", status_code=503
            )
        schema_prompt = (
            f"{prompt}\n\nВерни только валидный JSON без markdown и комментариев по схеме:\n"
            f"{json.dumps(response_model.model_json_schema(), ensure_ascii=False)}"
        )
        try:
            response = await self._client.achat.create(
                {
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": schema_prompt},
                    ],
                    "model_options": {"temperature": temperature, "max_tokens": max_tokens},
                }
            )
            text = _response_text(response)
            return response_model.model_validate_json(_extract_json(text))
        except Exception as exc:
            raise ServiceError(
                "gigachat",
                "ИИ не смог вернуть корректный структурированный ответ",
                details=f"{type(exc).__name__}: {exc}",
            ) from exc


def _response_text(response: object) -> str:
    messages = getattr(response, "messages", None) or []
    if not messages:
        return ""
    parts = getattr(messages[0], "content", None) or []
    return "".join((getattr(part, "text", None) or "") for part in parts)


def _extract_json(text: str) -> str:
    stripped = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", stripped, re.DOTALL)
    if fenced:
        return fenced.group(1)
    start = stripped.find("{")
    end = stripped.rfind("}")
    return stripped[start: end + 1] if start >= 0 and end > start else stripped
