from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.models import OriginCity, TripRequest
from src.sample import sample_trip
from src.services import destinations
from src.services.destinations import (
    DestinationCandidate,
    DestinationCandidates,
    choose_destination,
)
from src.services.gigachat_ai import GigaChatService


def candidates(*values):
    return DestinationCandidates(candidates=[DestinationCandidate(
        name=name, region="Московская область", reason="Подходит под интересы и длительность поездки.",
        fit_score=score) for name, score in values])


def test_new_comparable_cities_win_over_recent_ones(monkeypatch):
    pool = []
    monkeypatch.setattr(destinations.random, "choice", lambda items: (pool.extend(items), items[0])[1])
    result = choose_destination(candidates(("Коломна", 96), ("Зарайск", 91), ("Тула", 60)), "Москва", ["г. Коломна, Московская область"])
    assert result.name == "Зарайск"
    assert [item.name for item in pool] == ["Зарайск"]
    assert "fit_score" not in result.model_dump()


def test_narrow_request_is_more_important_than_novelty():
    assert choose_destination(candidates(("Клин", 99), ("Зарайск", 60)), "Москва", ["Клин"]).name == "Клин"


def test_origin_and_duplicates_are_removed_and_visited_pool_remains_usable(monkeypatch):
    pool = []
    monkeypatch.setattr(destinations.random, "choice", lambda items: (pool.extend(items), items[0])[1])
    result = choose_destination(candidates(("Москва", 100), ("Клин", 90), ("г. Клин", 89), ("Истра", 90)), "Москва", ["Клин", "Истра"])
    assert result.name in {"Клин", "Истра"}
    assert len(pool) == 2


def test_origin_hints_are_broad_and_unique():
    for origin in OriginCity:
        hints = destinations.DESTINATION_HINTS[origin]
        assert len(hints) >= 20
        assert len(hints) == len(set(hints))
        assert origin.value not in hints


@pytest.mark.asyncio
async def test_prompt_contains_preferences_history_and_origin_specific_options():
    service = GigaChatService(credentials=None, scope="", model="", verify_ssl_certs=True, ca_bundle_file=None, timeout=10)
    service._structured = AsyncMock(return_value=candidates(("Приозерск", 95)))
    request = TripRequest(origin="Санкт-Петербург", preferences="Хочу увидеть крепость и озеро", has_car=True)
    result = await service.suggest_destination(request, ["Выборг"])
    assert result.name == "Приозерск"
    call = service._structured.call_args.kwargs
    assert request.preferences in call["prompt"]
    assert '"Выборг"' in call["prompt"] and '"Гатчина"' in call["prompt"]
    assert '"Таруса"' not in call["prompt"]
    assert call["temperature"] == destinations.DESTINATION_TEMPERATURE


@pytest.mark.asyncio
async def test_trip_generation_keeps_low_temperature():
    service = GigaChatService(credentials=None, scope="", model="", verify_ssl_certs=True, ca_bundle_file=None, timeout=10)
    service._structured = AsyncMock()
    await service.build_trip(TripRequest(), destination_name="Клин", facts={})
    assert "temperature" not in service._structured.call_args.kwargs


@pytest.mark.asyncio
async def test_recent_destinations_are_owner_scoped_and_ordered(store):
    from datetime import timedelta
    plan = sample_trip()
    for index, name in enumerate(("Клин", "Истра", "Зарайск")):
        item = plan.model_copy(deep=True)
        item.id = uuid4()
        item.created_at += timedelta(seconds=index)
        item.destination.title = name
        await store.put(item, "max:42")
    foreign = plan.model_copy(update={"id": uuid4()})
    await store.put(foreign, "max:43")
    assert await store.recent_destinations("max:42", 2) == ["Зарайск", "Истра"]
    assert await store.recent_destinations("max:unknown", 8) == []


@pytest.mark.asyncio
async def test_job_only_reads_history_for_automatic_choice():
    from src.jobs import TripJobManager
    from src.models import JobState, TripJobStatus
    store = SimpleNamespace(
        recent_destinations=AsyncMock(return_value=["Коломна"]),
        update_job=AsyncMock(), finish_job=AsyncMock(),
    )
    planner = SimpleNamespace(generate=AsyncMock(return_value=sample_trip()))
    manager = TripJobManager(planner, store)
    for destination in (None, "Клин"):
        job = TripJobStatus(id=uuid4(), status=JobState.QUEUED, progress=0, message="Ожидание", events=[])
        await manager._run(job, TripRequest(destination=destination), "max:42")
        assert planner.generate.call_args.kwargs["recent_destinations"] == (["Коломна"] if destination is None else [])
    store.recent_destinations.assert_awaited_once_with("max:42", destinations.RECENT_DESTINATION_LIMIT)
