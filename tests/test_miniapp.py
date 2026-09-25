import asyncio
import re
from types import SimpleNamespace

import httpx
import pytest

from src.api.routes import get_container
from src.app import app
from src.config import Settings, get_settings
from src.errors import ServiceError
from src.jobs import TripJobManager
from src.models import TripRequest
from src.sample import sample_trip
from tests.test_auth import TOKEN, signed_data


class SamplePlanner:
    def __init__(self, store):
        self.store = store

    async def generate(self, request, progress=None, owner_id=None):
        if progress:
            await progress(65, "Проверка сценария")
        plan = sample_trip()
        return plan


@pytest.mark.asyncio
async def test_full_api_job_flow_and_cross_user_isolation(store):
    planner = SamplePlanner(store)
    jobs = TripJobManager(planner, store)
    container = SimpleNamespace(store=store, planner=planner, jobs=jobs)
    app.dependency_overrides[get_container] = lambda: container
    app.dependency_overrides[get_settings] = lambda: Settings(
        _env_file=None, max_bot_token=TOKEN
    )
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://localhost"
        ) as client:
            owner = {"X-Max-Init-Data": signed_data(user_id=42)}
            stranger = {"X-Max-Init-Data": signed_data(user_id=43)}
            assert (await client.post("/api/v1/trips/jobs", json={})).status_code == 401
            response = await client.post("/api/v1/trips/jobs", json={}, headers=owner)
            assert response.status_code == 202
            status_url = response.json()["status_url"]
            assert (await client.get(status_url, headers=stranger)).status_code == 404
            for _ in range(200):
                response = await client.get(status_url, headers=owner)
                if response.json()["status"] == "succeeded":
                    break
                await asyncio.sleep(0.01)
            result = response.json()
            assert result["status"] == "succeeded"
            history = await client.get("/api/v1/trips", headers=owner)
            assert history.json()["items"][0]["id"] == result["result"]["id"]
            assert (await client.get("/api/v1/trips", headers=stranger)).json()["items"] == []
            assert (await client.get("/api/v1/trips")).status_code == 401
            assert (await client.get("/api/v1/trips?limit=0", headers=owner)).status_code == 422
            trip_url = "/api/v1/trips/" + result["result"]["id"]
            for path in [trip_url, trip_url + "/share"]:
                assert (await client.get(path, headers=owner)).status_code == 200
                assert (await client.get(path, headers=stranger)).status_code == 404
                assert (await client.get(path)).status_code == 401
            assert (
                await client.get("/api/v1/examples/trip-plan", headers=owner)
            ).status_code == 404
            assert (
                await client.post(
                    "/api/v1/trips/jobs", json={"days": 100}, headers=owner
                )
            ).status_code == 422
    finally:
        await jobs.close()
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_trips_are_not_evicted_and_preserve_ownership(store):
    first = sample_trip()
    await store.put(first, owner_id="max:42")
    assert await store.get(first.id) is None
    assert await store.get(first.id, owner_id="max:43") is None
    assert await store.get(first.id, owner_id="max:42") is not None
    from uuid import uuid4

    second = first.model_copy(update={"id": uuid4()})
    await store.put(second, owner_id="max:43")
    assert (await store.get(first.id, owner_id="max:42")).model_dump(mode="json") == first.model_dump(mode="json")
    assert (await store.list("max:42")).total == 1


@pytest.mark.asyncio
async def test_active_job_limits_and_same_user_deduplication(store):
    class WaitingPlanner:
        async def generate(self, *args, **kwargs):
            await asyncio.Event().wait()

    jobs = TripJobManager(WaitingPlanner(), store, max_active=2)
    try:
        await jobs.submit(TripRequest(), owner_id="max:1")
        with pytest.raises(ServiceError) as error:
            await jobs.submit(TripRequest(), owner_id="max:1")
        assert error.value.status_code == 429
        await jobs.submit(TripRequest(), owner_id="max:2")
        with pytest.raises(ServiceError):
            await jobs.submit(TripRequest(), owner_id="max:3")
    finally:
        await jobs.close()


@pytest.mark.asyncio
async def test_miniapp_static_and_config_are_served_without_secrets():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://localhost"
    ) as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert 'id="root"' in response.text
        assert "https://st.max.ru/js/max-web-app.js" in response.text
        asset = re.search(r'src="(/static/assets/[^\"]+\.js)"', response.text)
        assert asset is not None
        assert (await client.get(asset[1])).status_code == 200
        config = (await client.get("/api/v1/app-config")).json()
        assert "token" not in str(config).lower()
        assert config["today"] < config["default_date"] <= config["last_trip_date"]
