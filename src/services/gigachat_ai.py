from __future__ import annotations

import json
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

    async def suggest_destination(self, request: TripRequest) -> DestinationSuggestion:
        prompt = f"""
Подбери ОДНО направление для короткой поездки по России. Точка должна быть реальным
городом менее чем в {SUGGESTED_CITY_DISTANCE_KM} км по прямой от точки отправления,
который однозначно находится русским геокодером. Не выбирай
точку отправления и не придумывай достопримечательности.

Анкета:
{request.model_dump_json(indent=2)}

Ограничения: дорога в одну сторону примерно не больше {request.max_travel_minutes} минут,
бюджет на всю группу {request.budget_rub} рублей. В region укажи субъект РФ.
""".strip()
        return await self._structured(
            DestinationSuggestion,
            system="Ты — эксперт по локальному туризму в России. Отвечай фактологично.",
            prompt=prompt,
            max_tokens=900,
        )

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
                    "model_options": {"temperature": 0.2, "max_tokens": max_tokens},
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
