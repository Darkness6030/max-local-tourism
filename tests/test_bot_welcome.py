from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI
from pydantic import SecretStr

from src.api import bot
from src.config import Settings
from src.errors import ServiceError
from src.services import bot_welcome as welcome


def settings():
    return Settings(
        _env_file=None,
        max_bot_token=SecretStr("test-token"),
        max_bot_username="test_bot",
        max_webhook_secret=SecretStr("test-secret"),
    )


def started():
    return {
        "update_type": "bot_started",
        "timestamp": 1234,
        "chat_id": 8,
        "user": {
            "user_id": 42,
            "first_name": "Тест",
            "last_activity_time": 0,
            "is_bot": False,
        },
    }


def command(value="/start", chat_type="dialog", is_bot=False):
    return {
        "update_type": "message_created",
        "timestamp": 1234,
        "message": {
            "sender": {
                "user_id": 42,
                "first_name": "Тест",
                "last_activity_time": 0,
                "is_bot": is_bot,
            },
            "timestamp": 1234,
            "recipient": {"chat_type": chat_type},
            "body": {"mid": "msg1", "seq": 1, "text": value},
        },
    }


def test_start_selection():
    assert welcome.welcome_recipient(started(), "test_bot") == 42
    for value in ("/start", "/start payload", "/start@test_bot"):
        assert welcome.welcome_recipient(command(value), "test_bot") == 42
    for event in (
        command("hello"),
        command("/starting"),
        command("/start@other_bot"),
        command(chat_type="chat"),
        command(is_bot=True),
        {"update_type": "bot_stopped"},
    ):
        assert welcome.welcome_recipient(event, "test_bot") is None



@pytest.mark.asyncio
async def test_webhook_auth_and_dispatch(monkeypatch):
    app = FastAPI()
    app.include_router(bot.router)
    monkeypatch.setattr(bot, "get_settings", settings)
    handler = AsyncMock()
    monkeypatch.setattr(bot, "handle_welcome", handler)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        for secret in ("", "wrong"):
            response = await client.post(
                "/api/v1/bot/webhook",
                json=started(),
                headers={"X-Max-Bot-Api-Secret": secret},
            )
            assert response.status_code == 403
        handler.assert_not_awaited()
        headers = {"X-Max-Bot-Api-Secret": "test-secret"}
        for event in ([], "event", 42):
            assert (
                await client.post("/api/v1/bot/webhook", json=event, headers=headers)
            ).status_code == 400
        response = await client.post(
            "/api/v1/bot/webhook", json=started(), headers=headers
        )
        assert response.status_code == 200
        handler.assert_awaited_once()
        monkeypatch.setattr(bot, "get_settings", lambda: Settings(_env_file=None))
        assert (
            await client.post("/api/v1/bot/webhook", json=started(), headers=headers)
        ).status_code == 503


@pytest.mark.asyncio
async def test_webhook_sdk_validation(monkeypatch):
    app = FastAPI()
    app.include_router(bot.router)
    monkeypatch.setattr(bot, "get_settings", settings)
    send = AsyncMock()
    monkeypatch.setattr(welcome, "send_welcome", send)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = {"X-Max-Bot-Api-Secret": "test-secret"}
        for message in ([], {"body": []}):
            response = await client.post(
                "/api/v1/bot/webhook",
                json={"update_type": "message_created", "message": message},
                headers=headers,
            )
            assert response.status_code == 400
        response = await client.post(
            "/api/v1/bot/webhook",
            json={"update_type": "bot_stopped"},
            headers=headers,
        )
        assert response.status_code == 200
        send.assert_not_awaited()


@pytest.mark.asyncio
async def test_send_payload_and_safe_errors(monkeypatch):
    from aiohttp import web

    from tests.test_max_sdk import mock_max_api, sent_message

    async with mock_max_api(
        monkeypatch, lambda request: web.json_response(sent_message())
    ) as state:
        await welcome.send_welcome(settings(), 42)
        request = state.requests[0]
        assert request["path"] == "/messages"
        assert request["query"] == {"user_id": "42"}
        assert request["headers"]["Authorization"] == "test-token"
        assert request["body"] == {
            "text": welcome.WELCOME_TEXT,
            "attachments": [
                {
                    "type": "inline_keyboard",
                    "payload": {
                        "buttons": [
                            [
                                {
                                    "type": "open_app",
                                    "text": "Открыть Рядом",
                                    "web_app": "test_bot",
                                }
                            ]
                        ]
                    },
                }
            ],
        }
        state.reply = lambda request: web.Response(status=500, text="secret")
        with pytest.raises(ServiceError) as caught:
            await welcome.send_welcome(settings(), 42)
        assert "secret" not in caught.value.message


@pytest.mark.asyncio
async def test_welcome_without_database_and_retry_after_failure(monkeypatch):
    send = AsyncMock(side_effect=ServiceError("max", "temporary", status_code=503))
    monkeypatch.setattr(welcome, "send_welcome", send)
    with pytest.raises(ServiceError):
        await welcome.handle_welcome(started(), settings())
    send.side_effect = None
    await welcome.handle_welcome(started(), settings())
    send.assert_awaited_with(settings(), 42)
    await welcome.handle_welcome(command(), settings())
    assert send.await_count == 3
    await welcome.handle_welcome(command("Обычное сообщение"), settings())
    assert send.await_count == 3
