"""City configuration regression with a browser-only catalog; no external API calls."""

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import expect, sync_playwright

from scripts.check_ui import BRIDGE
from src.cities import CityCatalog, load_city_catalog
from src.models import ProfilePreferences
from src.sample import sample_trip


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8001")
    args = parser.parse_args()
    payload = load_city_catalog().model_dump(mode="json")
    payload["cities"][0]["enabled"] = False
    payload["cities"].append({"id": "test-city", "name": "Тестоград"})
    payload["default_origin"] = "test-city"
    config = {
        **CityCatalog.model_validate(payload).public(),
        "today": "2026-09-28", "default_date": "2026-09-29",
        "last_trip_date": "2026-10-10", "max_days": 3,
    }
    screenshots = Path("tmp/ui-check")
    screenshots.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.webkit.launch()
        for width in (320, 1360):
            errors = []
            profile = {
                "onboarding_completed": True,
                "preferences": ProfilePreferences(origin="Москва").model_dump(mode="json"),
            }
            plan = sample_trip().model_dump(mode="json")
            plan["request"]["origin"] = "Тестоград"
            train = {
                "departure": "2026-09-29T09:00:00+07:00", "arrival": "2026-09-29T11:00:00+07:00",
                "duration_minutes": 120, "from_station": "Тестоград", "to_station": "Тверь",
                "transport_type": "suburban", "has_transfers": False, "price_rub": None,
                "buy_url": "https://rasp.yandex.ru/", "map_url": None,
            }
            plan["transport"] = {"outbound": [train], "return_trip": [], "source_name": "Тестовое расписание"}

            def api(route):
                path = urlparse(route.request.url).path.split("/api/v1/", 1)[1]
                if path == "app-config":
                    route.fulfill(json=config)
                elif path == "auth/me":
                    route.fulfill(json={"mode": "max", "user": {"id": 42, "first_name": "Анна"}})
                elif path == "profile":
                    if route.request.method == "PUT":
                        profile["preferences"] = route.request.post_data_json
                    route.fulfill(json=profile)
                elif path.endswith("/import"):
                    route.fulfill(json=plan)
                elif path.endswith("/share"):
                    route.fulfill(json={"text": "Тестовая поездка"})
                elif path.endswith("/reminders"):
                    route.fulfill(json={"outbound": None, "return_trip": None, "available": False})
                else:
                    raise AssertionError(f"Unexpected API: {path}")

            context = browser.new_context(viewport={"width": width, "height": 844}, reduced_motion="reduce")
            context.route("https://st.max.ru/**", lambda route: route.fulfill(content_type="application/javascript", body=BRIDGE))
            context.route("**/api/v1/**", api)
            context.add_init_script("sessionStorage.setItem('nearby:v2:max:42:draft', " + json.dumps(json.dumps({"origin": "Москва"})) + ")")
            page = context.new_page()
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(args.base_url)
            origin = page.get_by_label("Город отправления", exact=True)
            expect(origin).to_have_value("Тестоград")
            expect(origin.locator("option")).to_have_text(["Санкт-Петербург", "Тестоград"])
            expect(page.locator('[data-ui="preset-section"]')).to_have_count(0)
            hero = page.locator('[data-ui="adventure-card"] > img')
            hero.evaluate("el => el.decode()")
            fallback = hero.get_attribute("src")
            origin.select_option("Санкт-Петербург")
            expect(page.locator('[data-ui="preset-card"]')).to_have_count(2)
            expect(hero).not_to_have_attribute("src", fallback)
            origin.select_option("Тестоград")
            expect(page.locator('[data-ui="preset-section"]')).to_have_count(0)
            page.get_by_role("button", name="Спланировать поездку", exact=True).click()
            expect(page.get_by_label("Город отправления", exact=True)).to_have_value("Тестоград")
            page.get_by_role("button", name="Закрыть анкету", exact=True).click()
            page.get_by_role("button", name="Открыть профиль", exact=True).click()
            panel = page.locator('[data-ui="profile-page"]')
            expect(panel.get_by_label("Город отправления", exact=True)).to_have_value("Тестоград")
            panel.get_by_label("Город отправления", exact=True).select_option("Санкт-Петербург")
            panel.get_by_label("Город отправления", exact=True).select_option("Тестоград")
            page.get_by_role("button", name="На главную", exact=True).click()
            expect(origin).to_have_value("Тестоград")
            assert profile["preferences"]["origin"] == "Тестоград"
            page.screenshot(path=str(screenshots / f"city-config-{width}.png"), full_page=True)
            page.goto(f"{args.base_url.rstrip('/')}/?WebAppStartParam=trip_{'a' * 32}")
            page.get_by_role("tab", name="Дорога", exact=True).click()
            expect(page.locator('[data-ui="city-ticket-note"]')).to_have_count(0)
            expect(page.get_by_text("09:00", exact=True)).to_be_visible()
            expect(page.get_by_text("11:00", exact=True)).to_be_visible()
            assert not errors, errors
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            context.close()
            print(f"Config-only city, disabled origin, profile, wizard and local timetable passed: {width}px")
        browser.close()


if __name__ == "__main__":
    main()
