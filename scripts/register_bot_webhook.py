"""Register the welcome webhook explicitly through the pinned MAX SDK."""

import argparse
import asyncio
import sys
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from maxapi.enums.update import UpdateType

from src.config import get_settings
from src.errors import ServiceError
from src.services.max_bot import max_bot

WELCOME_UPDATES = [UpdateType.BOT_STARTED, UpdateType.MESSAGE_CREATED]


async def register(url: str):
    settings = get_settings()
    if (
        not settings.max_bot_token
        or not settings.max_webhook_secret
        or not settings.max_bot_username
    ):
        raise SystemExit("Задайте MAX_BOT_TOKEN, MAX_BOT_USERNAME и MAX_WEBHOOK_SECRET")
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.query or parsed.fragment:
        raise SystemExit(
            "Webhook должен иметь публичный HTTPS URL без query и fragment"
        )
    async with max_bot(settings) as bot:
        subscriptions = await bot.get_subscriptions()
        if any(item.url != url for item in subscriptions.subscriptions):
            raise SystemExit(
                "Есть другая подписка: проверьте её назначение перед подключением новой"
            )
        response = await bot.subscribe_webhook(
            url=url,
            update_types=WELCOME_UPDATES,
            secret=settings.max_webhook_secret.get_secret_value(),
        )
        if not response.success:
            raise SystemExit("MAX не подтвердил регистрацию webhook")
        subscriptions = await bot.get_subscriptions()
        if not any(
            item.url == url and set(item.update_types or []) == set(WELCOME_UPDATES)
            for item in subscriptions.subscriptions
        ):
            raise SystemExit("MAX не подтвердил ожидаемые события webhook")
        print("Webhook зарегистрирован и проверен: bot_started, message_created")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    args = parser.parse_args()
    try:
        asyncio.run(register(args.url))
    except ServiceError:
        raise SystemExit(
            "Не удалось зарегистрировать webhook: проверьте сеть, CA и настройки"
        ) from None
