"""MAX SDK configured for the current Bot API and header authentication."""

import asyncio
import json
import ssl
from contextlib import asynccontextmanager

import aiohttp
from maxapi import Bot
from maxapi.exceptions.invalid_token import InvalidToken
from maxapi.exceptions.max import MaxConnection

from src.config import Settings, get_settings
from src.errors import ServiceError

MAX_API_BASE_URL = "https://platform-api2.max.ru"
MAX_REQUEST_TIMEOUT_SECONDS = 15
MAX_OPERATION_TIMEOUT_SECONDS = 18


def _without_none(value):
    """The pinned SDK emits optional nulls; the API expects absent optional fields."""
    if isinstance(value, dict):
        return {
            key: _without_none(item) for key, item in value.items() if item is not None
        }
    if isinstance(value, list):
        return [_without_none(item) for item in value]
    return value


class _SdkSession:
    """Keep SDK methods/models, with redirects disabled and sanitized HTTP errors."""

    def __init__(self, session: aiohttp.ClientSession):
        self.session = session

    async def request(self, method, url, **kwargs):
        if not isinstance(url, str) or not url.startswith("/") or url.startswith("//"):
            raise ValueError("Expected a relative Bot API path")
        if "json" in kwargs:
            kwargs["json"] = _without_none(kwargs["json"])
        response = await self.session.request(
            method, url, allow_redirects=False, **kwargs
        )
        if not 200 <= response.status < 300:
            # Raise before the SDK can log the raw provider response.
            response.release()
            raise ServiceError(
                "max", "Не удалось выполнить запрос к MAX", status_code=503
            )
        return response

    async def close(self):
        await self.session.close()


@asynccontextmanager
async def max_bot(settings: Settings):
    if not settings.max_bot_token:
        raise ServiceError("max", "Не задан MAX_BOT_TOKEN", status_code=503)
    try:
        context = ssl.create_default_context()
        if settings.max_ca_bundle_file:
            context.load_verify_locations(cafile=settings.max_ca_bundle_file)
        # The webhook response must stay below MAX's 30-second deadline.
        async with asyncio.timeout(MAX_OPERATION_TIMEOUT_SECONDS):
            async with aiohttp.ClientSession(
                base_url=MAX_API_BASE_URL,
                headers={"Authorization": settings.max_bot_token.get_secret_value()},
                timeout=aiohttp.ClientTimeout(total=MAX_REQUEST_TIMEOUT_SECONDS),
                connector=aiohttp.TCPConnector(ssl=context),
            ) as session:
                bot = Bot(
                    settings.max_bot_token.get_secret_value(),
                    auto_requests=False,
                    auto_check_subscriptions=False,
                )
                bot.API_URL = MAX_API_BASE_URL
                bot.params = {}  # SDK defaults to access_token in the query string.
                bot.session = _SdkSession(session)
                yield bot
    except (
        aiohttp.ClientError,
        MaxConnection,
        InvalidToken,
        ValueError,
        TimeoutError,
        OSError,
    ):
        raise ServiceError(
            "max",
            "Не удалось выполнить запрос к MAX. Проверьте сеть, токен и CA-сертификат.",
            status_code=503,
        ) from None


async def get_bot_info(settings: Settings) -> dict:
    async with max_bot(settings) as bot:
        info = await bot.get_me()
        if not info.is_bot:
            raise ServiceError(
                "max", "MAX вернул неожиданный ответ о боте", status_code=503
            )
        return info.model_dump(include={"user_id", "username", "first_name", "is_bot"})


def main() -> None:
    try:
        data = asyncio.run(get_bot_info(get_settings()))
    except ServiceError as exc:
        raise SystemExit(exc.message) from None
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
