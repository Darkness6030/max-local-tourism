import pytest

from src.config import Settings


@pytest.fixture(autouse=True)
def isolate_process_settings(monkeypatch):
    """Do not let Docker's development env enable auth bypass in unit tests."""
    for name in Settings.model_fields:
        monkeypatch.delenv(name.upper(), raising=False)
        monkeypatch.delenv(name, raising=False)


import os
from uuid import uuid4

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from src.database import database_url
from src.store import TripStore

# Capture before the environment isolation fixture runs. Never use DATABASE_URL.
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")


@pytest_asyncio.fixture
async def store():
    if not TEST_DATABASE_URL:
        pytest.skip("Set TEST_DATABASE_URL to an isolated PostgreSQL database")
    schema = "test_" + uuid4().hex
    url = database_url(TEST_DATABASE_URL)
    admin = create_async_engine(url)
    async with admin.begin() as connection:
        await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_async_engine(url, connect_args={"server_settings": {"search_path": schema}})
    try:
        async with engine.begin() as connection:
            await connection.run_sync(SQLModel.metadata.create_all)
        yield TripStore(async_sessionmaker(engine, expire_on_commit=False))
    finally:
        await engine.dispose()
        async with admin.begin() as connection:
            await connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        await admin.dispose()
