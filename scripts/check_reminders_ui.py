"""Departure reminder controls with mocked API/MAX; no real notifications."""

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import expect, sync_playwright

from scripts.check_ui import BRIDGE
from src.cities import get_city_catalog
from src.sample import sample_trip


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8769")
    parser.add_argument("--browser", choices=["chrome", "webkit"], default="webkit")
    args = parser.parse_args()
    plan = sample_trip().model_dump(mode="json")
    now = datetime.now(timezone.utc)
    options = [{
        "departure": (now + timedelta(hours=2, minutes=i * 10)).isoformat(),
        "arrival": (now + timedelta(hours=3, minutes=i * 10)).isoformat(),
        "transport_type": "bus" if i else "suburban", "duration_minutes": 60,
        "from_station": "Москва", "to_station": "Коломна", "price_rub": 450,
        "has_transfers": False, "buy_url": "https://rasp.yandex.ru/",
    } for i in range(2)]
    options.append({**options[0], "departure": (now - timedelta(minutes=1)).isoformat()})
    plan["transport"] = {"outbound": options, "return_trip": options}
    token = "a" * 32
    state = {"outbound": None, "return_trip": None, "available": True}
    control = {"fail_get": True, "fail_put": False, "hold": False}
    pending = []
    writes = []

    def api(route):
        path = urlparse(route.request.url).path.split("/api/v1/", 1)[1]
        if "/reminders/" in path:
            assert route.request.method == "PUT"
            direction = path.rsplit("/", 1)[1]
            payload = route.request.post_data_json
            writes.append((direction, payload))
            if control["fail_put"]:
                route.fulfill(status=503, json={"error": "Не удалось сохранить напоминание"})
                return
            state[direction] = payload["option_index"]
            if control["hold"]:
                pending.append(route)
                return
            route.fulfill(json=state)
        elif path.endswith("/reminders"):
            if control["fail_get"]:
                control["fail_get"] = False
                route.fulfill(status=503, json={"error": "Temporary failure"})
            else:
                route.fulfill(json=state)
        elif path == "auth/me":
            route.fulfill(json={"mode": "max", "user": {"id": 42, "first_name": "Анна"}})
        elif path == "profile":
            route.fulfill(json={"onboarding_completed": True})
        elif path == "app-config":
            route.fulfill(json={"today": "2026-09-27", "default_date": "2026-09-28", "last_trip_date": "2026-10-10",
                                "max_days": 3, **get_city_catalog().public()})
        elif path.endswith("/share"):
            route.fulfill(json={"text": "Поездка"})
        elif path.endswith("/import"):
            route.fulfill(json=plan)
        else:
            raise AssertionError(f"Unexpected API: {path}")

    with sync_playwright() as p:
        browser = p.webkit.launch() if args.browser == "webkit" else p.chromium.launch(channel="chrome")
        context = browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
        if args.base_url == "http://127.0.0.1:8769":
            context.route("**/static/**", lambda r: r.fulfill(path=str(Path("src/static") / r.request.url.split("/static/", 1)[1])))
        context.route("https://st.max.ru/**", lambda r: r.fulfill(content_type="application/javascript", body=BRIDGE))
        context.route("**/api/v1/**", api)
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.clock.install(time=now)
        page.goto(f"{args.base_url.rstrip('/')}/?WebAppStartParam=trip_{token}")
        page.get_by_role("tab", name="Дорога").click()
        panel = page.locator('[data-ui="transport-panel"]')
        expect(panel.get_by_role("alert")).to_contain_text("Не удалось загрузить")
        panel.get_by_role("button", name="Повторить", exact=True).click()
        switches = panel.get_by_role("switch")
        expect(switches).to_have_count(4)
        expect(panel.get_by_text("Рейс уже отправился", exact=True)).to_have_count(2)
        expect(switches.nth(0)).to_be_enabled()
        expect(panel.get_by_role("button", name="Расписание")).to_have_count(2)
        intro = panel.get_by_text("Время рейсов из расписаний.", exact=False)
        assert intro.evaluate("el => Math.abs(parseFloat(getComputedStyle(el).lineHeight) / parseFloat(getComputedStyle(el).fontSize) - 1.7) < .01")
        control["hold"] = True
        switches.nth(0).click()
        expect(switches.nth(1)).to_be_disabled()
        assert len(writes) == 1
        pending.pop().fulfill(json=state)
        control["hold"] = False
        expect(switches.nth(0)).to_be_checked()
        switches.nth(1).click()
        expect(switches.nth(0)).not_to_be_checked()
        expect(switches.nth(1)).to_be_checked()
        switches.nth(2).click()
        expect(switches.nth(1)).to_be_checked()
        expect(switches.nth(2)).to_be_checked()
        switches.nth(3).click()
        expect(switches.nth(2)).not_to_be_checked()
        expect(switches.nth(3)).to_be_checked()
        page.reload()
        page.get_by_role("tab", name="Дорога").click()
        expect(switches.nth(1)).to_be_checked()
        expect(switches.nth(3)).to_be_checked()
        control["fail_put"] = True
        switches.nth(0).click()
        expect(panel.get_by_role("alert")).to_contain_text("Не удалось сохранить")
        expect(switches.nth(0)).to_be_enabled()
        expect(switches.nth(0)).not_to_be_checked()
        expect(switches.nth(1)).to_be_checked()
        control["fail_put"] = False
        switches.nth(1).click()
        expect(switches.nth(1)).not_to_be_checked()
        expect(switches.nth(3)).to_be_checked()
        for width in (390, 320):
            page.set_viewport_size({"width": width, "height": 844})
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            for switch in switches.all():
                assert switch.evaluate("el => { const r=el.getBoundingClientRect(); return r.left >= 0 && r.right <= innerWidth; }")
        switches.nth(0).scroll_into_view_if_needed()
        Path("tmp").mkdir(exist_ok=True)
        page.screenshot(path=f"tmp/reminders-{args.browser}.png")
        # Crossing departure time replaces both selected and unselected switches without reload.
        before = len(writes)
        page.clock.fast_forward(2 * 60 * 60 * 1000)
        expect(switches).to_have_count(2)
        expect(panel.get_by_text("Рейс уже отправился", exact=True)).to_have_count(4)
        page.clock.fast_forward(10 * 60 * 1000)
        expect(switches).to_have_count(0)
        expect(panel.get_by_text("Рейс уже отправился", exact=True)).to_have_count(6)
        assert len(writes) == before  # Rendering a departed flight must not cancel its final notification.
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        assert not errors, errors
        browser.close()
    print(f"Reminders UI passed ({args.browser}): exclusive choices, both directions, reload, errors, 320/390 px, leading 1.7")


if __name__ == "__main__":
    main()
