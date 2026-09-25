from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest
from aiohttp import web

from scripts import register_bot_webhook
from src.errors import ServiceError
from src.services import max_bot as sdk
from tests.test_bot_welcome import settings

BOT_INFO = {
    "user_id": 9,
    "first_name": "Рядом",
    "username": "test_bot",
    "is_bot": True,
    "last_activity_time": 0,
}


def sent_message():
    return {
        "message": {
            "sender": BOT_INFO,
            "recipient": {"user_id": 42, "chat_type": "dialog"},
            "timestamp": 1234,
            "body": {"mid": "sent", "seq": 1, "text": "Привет"},
        }
    }


@asynccontextmanager
async def mock_max_api(monkeypatch, reply):
    state = SimpleNamespace(requests=[], reply=reply)

    async def handle(request):
        body = await request.json() if request.can_read_body else None
        state.requests.append(
            {
                "method": request.method,
                "path": request.path,
                "query": dict(request.query),
                "headers": dict(request.headers),
                "body": body,
            }
        )
        return state.reply(request)

    app = web.Application()
    app.router.add_route("*", "/{path:.*}", handle)
    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = runner.addresses[0][1]
    monkeypatch.setattr(sdk, "MAX_API_BASE_URL", f"http://127.0.0.1:{port}")
    try:
        yield state
    finally:
        await runner.cleanup()


@pytest.mark.asyncio
async def test_sdk_get_me_header_auth_no_token_query_and_session_closes(monkeypatch):
    async with mock_max_api(
        monkeypatch, lambda request: web.json_response(BOT_INFO)
    ) as state:
        info = await sdk.get_bot_info(settings())
        assert info == {
            k: BOT_INFO[k] for k in ("user_id", "username", "first_name", "is_bot")
        }
        request = state.requests[0]
        assert request["path"] == "/me" and request["query"] == {}
        assert request["headers"]["Authorization"] == "test-token"
        async with sdk.max_bot(settings()) as bot:
            session = bot.session.session
            assert not session.closed
        assert session.closed


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [302, 401, 429, 500])
async def test_sdk_never_follows_redirects_or_logs_provider_errors(
    monkeypatch, caplog, status
):
    async with mock_max_api(
        monkeypatch,
        lambda request: web.Response(
            status=status,
            headers={"Location": "/leak"},
            text="secret-provider-response",
        ),
    ) as state:
        with pytest.raises(ServiceError) as caught:
            await sdk.get_bot_info(settings())
        assert len(state.requests) == 1
        assert "secret" not in str(caught.value) + caplog.text


@pytest.mark.asyncio
async def test_register_uses_sdk_and_preserves_update_types(monkeypatch):
    monkeypatch.setattr(register_bot_webhook, "get_settings", settings)
    url = "https://example.com/api/v1/bot/webhook"
    subscription = {
        "url": url,
        "time": 1234,
        "update_types": ["bot_started", "message_created"],
    }

    def reply(request):
        return web.json_response(
            {"success": True}
            if request.method == "POST"
            else {"subscriptions": [subscription]}
        )

    async with mock_max_api(monkeypatch, reply) as state:
        await register_bot_webhook.register(url)
        assert [r["method"] for r in state.requests] == ["GET", "POST", "GET"]
        assert state.requests[1]["body"] == {
            "url": url,
            "update_types": ["bot_started", "message_created"],
            "secret": "test-secret",
        }
        assert all(
            r["query"] == {} and r["headers"]["Authorization"] == "test-token"
            for r in state.requests
        )


@pytest.mark.asyncio
async def test_register_does_not_overwrite_other_subscription(monkeypatch):
    monkeypatch.setattr(register_bot_webhook, "get_settings", settings)
    async with mock_max_api(
        monkeypatch,
        lambda request: web.json_response(
            {"subscriptions": [{"url": "https://other.example/webhook", "time": 1234}]}
        ),
    ) as state:
        with pytest.raises(SystemExit):
            await register_bot_webhook.register("https://example.com/webhook")
        assert len(state.requests) == 1 and state.requests[0]["method"] == "GET"
