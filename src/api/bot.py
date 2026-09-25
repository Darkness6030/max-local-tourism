"""MAX webhook: authenticated independently of miniapp initData."""

import hmac
import json

from fastapi import APIRouter, HTTPException, Request
from pydantic import ValidationError

from src.config import get_settings
from src.services.bot_welcome import handle_welcome

router = APIRouter()


@router.post("/api/v1/bot/webhook", include_in_schema=False)
async def bot_webhook(request: Request):
    settings = get_settings()
    secret = settings.max_webhook_secret
    if not secret or not settings.max_bot_token or not settings.max_bot_username:
        raise HTTPException(503, "Webhook не настроен")

    supplied = request.headers.get("X-Max-Bot-Api-Secret", "")
    if not hmac.compare_digest(supplied.encode(), secret.get_secret_value().encode()):
        raise HTTPException(403, "Неверный секрет webhook")

    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > 256_000:
            raise HTTPException(413, "Слишком большое событие")

    try:
        update = json.loads(body)
    except (ValueError, TypeError):
        raise HTTPException(400, "Некорректное событие") from None

    if not isinstance(update, dict):
        raise HTTPException(400, "Некорректное событие")

    try:
        await handle_welcome(update, settings)
    except ValidationError:
        raise HTTPException(400, "Некорректное событие MAX") from None

    return {"success": True}
