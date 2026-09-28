"""Offline browser checks for accommodation states and narrow layouts."""

import argparse
import copy
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from playwright.sync_api import sync_playwright

from scripts.check_ui import BRIDGE, mock_profile
from src.cities import get_city_catalog
from src.models import current_date, default_trip_date
from src.sample import sample_trip


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:18092")
    args = parser.parse_args()
    plan = sample_trip().model_dump(mode="json")
    plan["request"]["days"] = 2
    stay = {
        "check_in": plan["request"]["start_date"],
        "check_out": str(date.fromisoformat(plan["request"]["start_date"]) + timedelta(days=1)),
        "nights": 1,
        "rooms": 1,
        "estimated_room_night_rub": 6000,
        "estimated_total_rub": 6000,
        "status": "found",
        "fetched_at": None,
        "search_url": "https://yandex.ru/maps/?text=Гостиницы",
        "hotels": [
            {
                "id": "node/1",
                "name": "Гостиница в историческом центре",
                "kind": "hotel",
                "address": "Улица Октябрьской революции, 200",
                "distance_km": 0.7,
                "website": "https://example.com/hotel",
                "map_url": "https://yandex.ru/maps/?pt=38.76,55.09",
                "source_url": "https://www.openstreetmap.org/node/1",
            }
        ],
    }
    config = {
        "today": str(current_date()),
        "default_date": str(default_trip_date()),
        "last_trip_date": str(default_trip_date()),
        "max_days": 3,
        **get_city_catalog().public(),
        "bot_url": None,
    }
    output = Path("tmp/hotels-ui")
    output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        for width, state in [
            (320, "found"),
            (390, "found"),
            (390, "two-nights"),
            (1360, "found"),
            (390, "empty"),
            (390, "unavailable"),
            (390, "one-day"),
            (390, "legacy"),
        ]:
            fixture = copy.deepcopy(plan)
            fixture["accommodation"] = copy.deepcopy(stay)
            if state == "two-nights":
                fixture["accommodation"]["nights"] = 2
                fixture["request"]["days"] = 3
            if state in {"empty", "unavailable"}:
                fixture["accommodation"].update(status=state, hotels=[])
            if state == "one-day":
                fixture["request"]["days"] = 1
            if state == "legacy":
                fixture.pop("accommodation")
            context = browser.new_context(
                viewport={"width": width, "height": 844}, reduced_motion="reduce"
            )
            mock_profile(context, completed=True)
            context.route(
                "https://st.max.ru/**",
                lambda r: r.fulfill(content_type="application/javascript", body=BRIDGE),
            )
            context.route(
                "**/api/v1/auth/me",
                lambda r: r.fulfill(
                    json={"mode": "max", "user": {"id": 42, "first_name": "Анна"}}
                ),
            )
            context.route("**/api/v1/app-config", lambda r: r.fulfill(json=config))
            context.route(
                "**/api/v1/trips/jobs/result",
                lambda r, *, fixture=fixture: r.fulfill(
                    json={
                        "id": "result",
                        "status": "succeeded",
                        "progress": 100,
                        "message": "Готово",
                        "events": [],
                        "result": fixture,
                        "error": None,
                    }
                ),
            )
            context.add_init_script(
                "sessionStorage.setItem('nearby:v2:max:42:job',JSON.stringify('result'))"
            )
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda error, errors=errors: errors.append(str(error)))
            page.goto(args.base_url, wait_until="networkidle")
            card = page.locator('[data-ui="accommodation-card"]')
            if state in {"legacy", "one-day"}:
                assert card.count() == 0
            else:
                card.scroll_into_view_if_needed()
                assert card.is_visible()
                assert "6\u00a0000" in card.inner_text()
                assert "Цены и свободные номера" in card.inner_text()
                assert "ноч." not in card.inner_text()
                assert ("2 ночи" if state == "two-nights" else "1 ночь") in card.inner_text()
                if state in {"found", "two-nights"}:
                    page.get_by_role("link", name="Сайт гостиницы").click()
                    assert "https://example.com/hotel" in page.evaluate(
                        "window.WebApp.calls"
                    )
                    assert page.locator('[data-ui="hotel-card"]').count() == 1
                else:
                    assert page.locator('[data-ui="hotel-empty"]').is_visible()
                card.screenshot(path=str(output / f"{width}-{state}.png"))
            assert not page.evaluate(
                "document.documentElement.scrollWidth > innerWidth"
            )
            assert not errors, errors
            print(width, state, "OK")
            context.close()
        browser.close()


if __name__ == "__main__":
    main()
