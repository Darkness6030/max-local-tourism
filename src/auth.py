"""MAX launch data verification; development access is explicit and loopback-only."""

import hashlib
import hmac
import json
import re
import time
from typing import Annotated, Literal
from urllib.parse import parse_qsl

from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from src.config import Settings, get_settings

launch_data_header = APIKeyHeader(
    name="X-Max-Init-Data",
    scheme_name="MaxInitData",
    auto_error=False,
    description="Исходная window.WebApp.initData; подпись и срок действия проверяются сервером.",
)


class MaxUser(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int = Field(strict=True, gt=0)
    first_name: str = Field(min_length=1, max_length=200)
    last_name: str | None = None
    username: str | None = None
    photo_url: str | None = None

    @field_validator("photo_url")
    @classmethod
    def safe_photo(cls, value: str | None) -> str | None:
        if value and value.startswith("https://") and len(value) <= 4096:
            return value
        return None


class Identity(BaseModel):
    mode: Literal["max", "local"]
    user: MaxUser

    @property
    def owner_id(self) -> str:
        return f"{self.mode}:{self.user.id}"


def validate_init_data(
    raw: str, token: str, *, ttl_seconds: int = 3600, now: float | None = None
) -> MaxUser:
    """Verify the raw query string once, before trusting user or other fields.

    Contract: https://dev.max.ru/docs/webapps/validation
    TTL and 30-second future tolerance are application policy.
    """
    try:
        if not raw or len(raw) > 16384 or re.search(r"%(?![0-9a-fA-F]{2})", raw):
            raise ValueError("Invalid encoding or length")
        pairs = parse_qsl(
            raw,
            keep_blank_values=True,
            strict_parsing=True,
            encoding="utf-8",
            errors="strict",
            max_num_fields=50,
        )
        fields = dict(pairs)
        if len(fields) != len(pairs) or any(not key for key in fields):
            raise ValueError("Duplicate or empty key")
        supplied_hash = fields.pop("hash")
        if not re.fullmatch(r"[0-9a-fA-F]{64}", supplied_hash):
            raise ValueError("Invalid hash")
        check_string = "\n".join(
            f"{key}={value}" for key, value in sorted(fields.items())
        )
        secret = hmac.digest(b"WebAppData", token.encode(), hashlib.sha256)
        expected = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, supplied_hash.lower()):
            raise ValueError("Signature mismatch")
        auth_date = int(fields["auth_date"])
        age = (time.time() if now is None else now) - auth_date
        if age < -30 or age > ttl_seconds:
            raise ValueError("Expired or future launch data")
        return MaxUser.model_validate(json.loads(fields["user"]))
    except (ValueError, KeyError, TypeError, UnicodeError, ValidationError) as exc:
        raise HTTPException(
            status_code=401,
            detail="Сессия MAX недействительна или истекла. Откройте приложение заново.",
        ) from exc


def local_access_allowed(request: Request, settings: Settings) -> bool:
    # Do not trust X-Forwarded-For. Run local uvicorn with proxy headers disabled.
    allowed_hosts = {"127.0.0.1", "localhost", "::1"}
    origin = request.headers.get("origin")
    return bool(
        settings.app_env in {"development", "test"}
        and settings.max_allow_local_auth
        and request.client
        and request.client.host in settings.max_local_client_hosts
        and request.url.hostname in allowed_hosts
        and (not origin or origin == f"{request.url.scheme}://{request.url.netloc}")
        and request.headers.get("sec-fetch-site") not in {"cross-site"}
    )


async def current_identity(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    launch_data: Annotated[str | None, Security(launch_data_header)],
) -> Identity:
    raw = request.headers.get("x-max-init-data")
    if raw is not None:
        if not settings.max_bot_token:
            raise HTTPException(
                status_code=503, detail="Токен MAX не настроен на сервере"
            )
        user = validate_init_data(
            raw,
            settings.max_bot_token.get_secret_value(),
            ttl_seconds=settings.max_init_data_ttl_seconds,
        )
        return Identity(mode="max", user=user)
    if local_access_allowed(request, settings):
        return Identity(mode="local", user=MaxUser(id=1, first_name="Локальный гость"))
    raise HTTPException(status_code=401, detail="Откройте мини-приложение из MAX")


IdentityDep = Annotated[Identity, Depends(current_identity)]
