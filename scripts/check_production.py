"""Deployment checks using explicitly synthetic signed launch data.

No MAX account is impersonated and no message is sent. --generate performs one
real trip generation, using external provider quotas. Never print launch data.
"""

import argparse
import hashlib
import hmac
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlencode, urljoin, urlsplit

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config import get_settings


def launch_data(token, user_id=900000000042):
    fields = {
        "auth_date": str(int(time.time())),
        "query_id": "deployment-check",
        "user": json.dumps(
            {
                "id": user_id,
                "first_name": "Проверка",
                "last_name": "развёртывания",
                "username": "deployment_check",
                "photo_url": None,
            },
            ensure_ascii=False,
        ),
    }
    secret = hmac.digest(b"WebAppData", token.encode(), hashlib.sha256)
    fields["hash"] = hmac.new(
        secret,
        "\n".join(f"{k}={v}" for k, v in sorted(fields.items())).encode(),
        hashlib.sha256,
    ).hexdigest()
    return urlencode(fields)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://kaktut.ru/max/app")
    parser.add_argument("--generate", action="store_true")
    args = parser.parse_args()
    settings = get_settings()
    token = settings.max_bot_token.get_secret_value()
    headers = {"X-Max-Init-Data": launch_data(token)}
    base = args.base_url.rstrip("/")
    with httpx.Client(timeout=30, follow_redirects=False) as client:

        def get(path, **kwargs):
            return client.get(base + path, **kwargs)

        page = get("")
        assert page.status_code == 200
        assets = re.findall(r'(?:src|href)="(/max/app/static/[^\"]+)"', page.text)
        assert len(assets) >= 2
        for asset in assets:
            if not urlsplit(base).path.strip("/"):
                asset = asset.removeprefix("/max/app")
            response = client.get(urljoin(base, asset))
            assert response.status_code == 200, asset
        assert get("/api/v1/auth/me").status_code == 401
        assert (
            get("/api/v1/auth/me", headers={"X-Max-Init-Data": "invalid"}).status_code
            == 401
        )
        assert get("/api/v1/profile").status_code == 401
        profile = get("/api/v1/profile", headers=headers)
        profile.raise_for_status()
        assert isinstance(profile.json()["onboarding_completed"], bool)
        identity = get("/api/v1/auth/me", headers=headers)
        identity.raise_for_status()
        assert identity.json()["mode"] == "max"
        assert identity.json()["user"]["id"] == 900000000042
        assert identity.json()["user"]["last_name"] == "развёртывания"
        assert "no-store" in identity.headers.get("cache-control", "")
        for path in (
            "/api/v1/examples/trip-plan",
            "/api/v1/examples/trip-request",
            "/docs",
            "/openapi.json",
            "/api/v1/geocode",
        ):
            assert get(path, headers=headers).status_code == 404, path
        assert client.post(base + "/api/v1/trips/jobs", json={}).status_code == 401
        assert (
            client.post(
                base + "/api/v1/trips/jobs", headers=headers, json={"days": 999}
            ).status_code
            == 422
        )
        print(
            "Production: no guest access; verified profile accepted; invalid signatures rejected; development routes closed.",
            flush=True,
        )
        if not args.generate:
            return
        config = get("/api/v1/app-config").json()
        start = time.monotonic()
        created = client.post(
            base + "/api/v1/trips/jobs",
            headers=headers,
            json={
                "origin": "Москва",
                "destination": "Коломна",
                "start_date": config["default_date"],
                "days": 1,
                "travelers": 2,
                "budget_rub": 12000,
                "preferences": "Прогулки, история, местная кухня",
                "has_car": False,
            },
        )
        created.raise_for_status()
        job_id = created.json()["id"]
        assert created.json()["status_url"].startswith("/max/app/api/v1/trips/jobs/")
        stranger = {"X-Max-Init-Data": launch_data(token, 900000000043)}
        assert get(f"/api/v1/trips/jobs/{job_id}", headers=stranger).status_code == 404
        previous = None
        while time.monotonic() - start < 260:
            response = get(f"/api/v1/trips/jobs/{job_id}", headers=headers)
            response.raise_for_status()
            job = response.json()
            if job["message"] != previous:
                print(f"{job['progress']}%: {job['message']}", flush=True)
                previous = job["message"]
            if job["status"] == "failed":
                raise RuntimeError(job["error"]["error"])
            if job["status"] == "succeeded":
                result = job["result"]
                assert (
                    get(f"/api/v1/trips/{result['id']}", headers=stranger).status_code
                    == 404
                )
                print(
                    json.dumps(
                        {
                            "trip_id": result["id"],
                            "elapsed_seconds": round(time.monotonic() - start, 1),
                            "days": len(result["itinerary"]),
                            "weather": result["weather"]["provider"],
                            "transport_found": bool(result["transport"]),
                            "owner_isolation": True,
                        },
                        ensure_ascii=False,
                    ),
                    flush=True,
                )
                return
            time.sleep(2)
        raise TimeoutError("Generation did not finish")


if __name__ == "__main__":
    main()
