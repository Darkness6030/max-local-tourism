import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import httpx
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from src.app import app
from src.auth import validate_init_data
from src.config import Settings, get_settings

TOKEN = "unit-test-token-not-a-real-secret"


def signed_data(user_id=42, auth_date=None, **extra):
    fields = {
        "auth_date": str(int(time.time()) if auth_date is None else auth_date),
        "query_id": "test-session",
        "user": json.dumps(
            {"id": user_id, "first_name": "Анна + % & ="}, ensure_ascii=False
        ),
        **extra,
    }
    secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
    body = "\n".join(f"{key}={value}" for key, value in sorted(fields.items()))
    fields["hash"] = hmac.new(secret, body.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


def test_signature_decodes_values_once_and_accepts_unicode():
    user = validate_init_data(signed_data(auth_date=1000), TOKEN, now=1100)
    assert user.id == 42
    assert user.first_name == "Анна + % & ="


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "hash=nope",
        "x=%ZZ&hash=aaa",
        "x=%ff&hash=aaa",
        signed_data(auth_date=1000) + "&hash=" + "0" * 64,
        signed_data(auth_date=1000) + "&user=another-user",
        signed_data(auth_date=1000).replace("test-session", "tampered"),
        signed_data(auth_date=1),
        signed_data(auth_date=10000),
        signed_data(user_id=True, auth_date=1000),
        signed_data(user_id="42", auth_date=1000),
        signed_data(auth_date=1000, user="[]"),
        signed_data(auth_date="wrong"),
    ],
)
def test_invalid_launch_data_is_rejected(raw):
    with pytest.raises(HTTPException) as error:
        validate_init_data(raw, TOKEN, now=1100, ttl_seconds=300)
    assert error.value.status_code == 401


def test_wrong_bot_token_is_rejected():
    with pytest.raises(HTTPException):
        validate_init_data(signed_data(), "different-token")


def test_verified_profile_includes_optional_max_fields_and_rejects_tampering():
    profile = {
        "id": 42,
        "first_name": "Анна",
        "last_name": "Иванова",
        "username": "anna",
        "photo_url": "https://example.com/avatar.jpg",
    }
    raw = signed_data(user=json.dumps(profile, ensure_ascii=False))
    user = validate_init_data(raw, TOKEN)
    assert user.last_name == "Иванова"
    assert user.username == "anna"
    assert user.photo_url == profile["photo_url"]
    with pytest.raises(HTTPException):
        validate_init_data(raw.replace("avatar.jpg", "other.jpg"), TOKEN)


@pytest.mark.parametrize(
    "photo", [None, "", "javascript:alert(1)", "http://example.com/a"]
)
def test_profile_without_a_safe_photo_keeps_identity(photo):
    raw = signed_data(
        user=json.dumps({"id": 42, "first_name": "Анна", "photo_url": photo})
    )
    user = validate_init_data(raw, TOKEN)
    assert user.id == 42
    assert user.photo_url is None


@pytest.mark.asyncio
@pytest.mark.parametrize("root_path", ["", "/max/app"])
async def test_verified_profile_is_never_cached_under_proxy_prefix(root_path):
    app.dependency_overrides[get_settings] = lambda: Settings(
        _env_file=None, max_bot_token=TOKEN
    )
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, root_path=root_path),
            base_url="https://kaktut.ru",
        ) as client:
            response = await client.get(
                root_path + "/api/v1/auth/me",
                headers={"X-Max-Init-Data": signed_data()},
            )
            assert response.status_code == 200
            assert response.json()["user"]["id"] == 42
            assert response.headers["Cache-Control"] == "no-store"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize(
    "values",
    [
        {"max_allow_local_auth": True, "max_bot_token": TOKEN},
        {"max_bot_token": None},
        {
            "max_bot_token": TOKEN,
            "gigachat_credentials": "test",
            "gigachat_verify_ssl_certs": False,
        },
    ],
)
def test_production_rejects_unsafe_configuration(values):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, app_env="production", **values)


@pytest.fixture
def local_settings():
    settings = Settings(
        _env_file=None, app_env="test", max_allow_local_auth=True, max_bot_token=TOKEN
    )
    app.dependency_overrides[get_settings] = lambda: settings
    yield settings
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "peer,host,headers,expected",
    [
        ("127.0.0.1", "127.0.0.1", {}, 200),
        ("203.0.113.4", "127.0.0.1", {"x-forwarded-for": "127.0.0.1"}, 401),
        ("127.0.0.1", "evil.example", {}, 401),
        ("127.0.0.1", "127.0.0.1", {"origin": "https://evil.example"}, 401),
        ("127.0.0.1", "127.0.0.1", {"sec-fetch-site": "cross-site"}, 401),
        ("127.0.0.1", "127.0.0.1", {"x-max-init-data": "bad-signature"}, 401),
        ("203.0.113.4", "app.example", {"x-max-init-data": signed_data()}, 200),
    ],
)
async def test_api_auth_never_downgrades_invalid_max_session(
    local_settings, peer, host, headers, expected
):
    transport = httpx.ASGITransport(app=app, client=(peer, 1234))
    async with httpx.AsyncClient(
        transport=transport, base_url=f"http://{host}"
    ) as client:
        response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == expected
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.asyncio
async def test_local_auth_disabled_by_default():
    app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None)
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1"
        ) as client:
            assert (await client.get("/api/v1/auth/me")).status_code == 401
    finally:
        app.dependency_overrides.clear()
