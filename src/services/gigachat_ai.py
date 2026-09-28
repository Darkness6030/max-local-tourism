from __future__ import annotations

import json
import random
import re
from typing import TypeVar

from gigachat import GigaChat
from pydantic import BaseModel

from src.cities import get_city_catalog
from src.constants import BUDGET_RESERVE_PERCENT
from src.errors import ServiceError
from src.models import (
    DestinationSuggestion,
    GeneratedTripContent,
    TripRequest,
)
from src.prompts import (
    DESTINATION_PROMPT,
    DESTINATION_SYSTEM_PROMPT,
    STRUCTURED_PROMPT,
    TRIP_PROMPT,
    TRIP_SYSTEM_PROMPT,
)
from src.services.destinations import (
    DESTINATION_CANDIDATE_COUNT,
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
        city = get_city_catalog().find(request.origin)
        hints = list(city.destination_hints) if city else []

        random.shuffle(hints)
        prompt = DESTINATION_PROMPT.format(
            candidate_count=DESTINATION_CANDIDATE_COUNT,
            request_json=request.model_dump_json(indent=2),
            hints_json=json.dumps(hints, ensure_ascii=False),
            recent_json=json.dumps(recent, ensure_ascii=False),
            distance_km=request.max_distance_km,
            origin=request.origin,
            max_travel_minutes=request.max_travel_minutes,
        )

        candidates = await self._structured(
            DestinationCandidates,
            system=DESTINATION_SYSTEM_PROMPT,
            prompt=prompt,
            max_tokens=2000,
            temperature=DESTINATION_TEMPERATURE,
        )

        return choose_destination(candidates, request.origin, recent)

    async def build_trip(
        self,
        request: TripRequest,
        *,
        destination_name: str,
        facts: dict,
    ) -> GeneratedTripContent:
        prompt = TRIP_PROMPT.format(
            destination_name=destination_name,
            request_json=request.model_dump_json(indent=2),
            facts_json=json.dumps(facts, ensure_ascii=False, indent=2, default=str),
            days=request.days,
            start_date=request.start_date,
            budget_rub=request.budget_rub,
            reserve_percent=BUDGET_RESERVE_PERCENT,
        )

        return await self._structured(
            GeneratedTripContent,
            system=TRIP_SYSTEM_PROMPT,
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

        schema_prompt = STRUCTURED_PROMPT.format(
            prompt=prompt,
            schema_json=json.dumps(response_model.model_json_schema(), ensure_ascii=False),
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
    return stripped[start: end + 1] if 0 <= start < end else stripped
