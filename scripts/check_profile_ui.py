"""Profile persistence, trip preferences and result layout; mocked API/MAX only."""

import argparse
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import expect, sync_playwright

from scripts.check_ui import BRIDGE
from src.models import ProfilePreferences
from src.sample import sample_trip


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:5173")
    parser.add_argument("--browser", choices=["chrome", "webkit"], default="webkit")
    args = parser.parse_args()
    screenshots = Path("tmp/ui-check")
    screenshots.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.webkit.launch() if args.browser == "webkit" else p.chromium.launch(channel="chrome")
        for width in (320, 390, 1360):
            profile = {"onboarding_completed": True, "preferences": ProfilePreferences(display_name="Старое имя", avatar_style="mountain").model_dump(mode="json")}
            control = {"fail": False}
            plan = sample_trip().model_dump(mode="json")
            plan["transport"] = None
            plan["request"]["days"] = 2
            plan["request"]["start_date"] = "2026-09-30"

            def api(route, *, control=control, profile=profile, plan=plan):
                path = urlparse(route.request.url).path.split("/api/v1/", 1)[1]
                if path == "profile":
                    if route.request.method == "PUT":
                        if control["fail"]:
                            route.fulfill(status=503, json={"error": "Не удалось сохранить настройки"})
                            return
                        profile["preferences"] = route.request.post_data_json
                    route.fulfill(json=profile)
                elif path == "auth/me":
                    route.fulfill(json={"mode": "max", "user": {"id": 42, "first_name": "Анна"}})
                elif path == "app-config":
                    route.fulfill(json={"today": "2026-09-27", "default_date": "2026-09-28", "last_trip_date": "2026-10-10",
                                        "max_days": 3, "origins": ["Москва", "Санкт-Петербург"]})
                elif path.endswith("/reminders"):
                    route.fulfill(json={"outbound": None, "return_trip": None, "available": True})
                elif path.endswith("/share"):
                    route.fulfill(json={"text": "Поездка"})
                elif path.endswith("/import"):
                    route.fulfill(json=plan)
                else:
                    raise AssertionError(f"Unexpected API: {path}")

            context = browser.new_context(viewport={"width": width, "height": 844}, reduced_motion="reduce")
            context.route("https://st.max.ru/**", lambda r: r.fulfill(content_type="application/javascript", body=BRIDGE))
            context.route("**/api/v1/**", api)
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda error, errors=errors: errors.append(str(error)))
            page.goto(args.base_url)
            expect(page.locator('[data-ui~="mood-card"]')).to_have_count(4)
            assert page.locator('[data-ui="adventure-caption"]').evaluate("""el => {
                const range = document.createRange(); range.selectNodeContents(el);
                const text = range.getBoundingClientRect();
                const button = el.previousElementSibling.getBoundingClientRect();
                const card = el.closest('[data-ui=adventure-card]').getBoundingClientRect();
                return Math.abs((text.top - button.bottom) - (card.bottom - text.bottom)) <= 2;
            }"""), "The caption must sit halfway between the button and the card bottom"
            page.screenshot(path=str(screenshots / f"home-moods-{args.browser}-{width}.png"), full_page=True)
            for title, interests in [("За местным вкусом", ["Местная кухня", "Прогулки"]),
                                     ("Больше движения", ["Активный отдых", "Природа"])]:
                page.get_by_role("button", name=title, exact=False).click()
                expect(page.get_by_label("Шаг 1 из 5", exact=True)).to_be_visible()
                assert page.evaluate("JSON.parse(sessionStorage.getItem('nearby:v2:max:42:draft')).interests") == interests
                page.get_by_role("button", name="Закрыть анкету", exact=True).click()
            page.get_by_role("button", name="Открыть профиль", exact=True).click()
            panel = page.locator('[data-ui="profile-page"]')
            expect(panel.get_by_role("heading", name="Профиль", exact=True)).to_be_visible()
            expect(page.get_by_label("Имя в приложении", exact=True)).to_have_count(0)
            expect(page.get_by_role("button", name="Горы", exact=True)).to_have_count(0)
            expect(panel.get_by_text("Анна", exact=True)).to_be_visible()
            expect(page.locator('[data-ui~="profile-preview"]')).to_have_text("А")
            panel.get_by_label("Дальность подбора городов", exact=True).fill("350")
            panel.get_by_label("Предпочтительный транспорт", exact=True).select_option("bus")
            panel.get_by_label("Город отправления", exact=True).select_option("Санкт-Петербург")
            panel.get_by_label("Темп поездок", exact=True).select_option("relaxed")
            page.get_by_role("button", name="История", exact=True).click()
            control["fail"] = True
            page.get_by_role("button", name="Сохранить настройки", exact=True).click()
            expect(panel.get_by_role("alert")).to_contain_text("Не удалось сохранить")
            expect(panel.get_by_label("Дальность подбора городов", exact=True)).to_have_value("350")
            control["fail"] = False
            page.get_by_role("button", name="Сохранить настройки", exact=True).click()
            expect(panel.get_by_role("button", name="Настройки сохранены", exact=True)).to_be_visible()
            expect(panel.get_by_role("status").filter(has_text="Настройки сохранены")).to_have_count(0)
            assert profile["preferences"]["max_distance_km"] == 350
            assert profile["preferences"]["preferred_transport"] == "bus"
            assert panel.evaluate("""el => getComputedStyle(el.querySelector('fieldset')).borderRadius ===
                getComputedStyle(el.querySelector('[data-ui~=profile-save]')).borderRadius""")
            assert profile["preferences"]["origin"] == "Санкт-Петербург"
            assert profile["preferences"]["pace"] == "relaxed"
            assert "История" in profile["preferences"]["interests"]
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            if width <= 700:
                for field in panel.locator("input:not([type=range]), select").all():
                    assert field.evaluate("el => parseFloat(getComputedStyle(el).fontSize) >= 16")
                    assert field.bounding_box()["height"] >= 51
            page.screenshot(path=str(screenshots / f"profile-{args.browser}-{width}.png"), full_page=True)
            page.get_by_role("button", name="Назад из профиля", exact=True).click()
            expect(page.get_by_label("Город отправления", exact=True)).to_have_value("Санкт-Петербург")
            # With no local draft, preferences must still come from the API.
            page.evaluate("sessionStorage.clear()")
            page.reload()
            expect(page.get_by_label("Город отправления", exact=True)).to_have_value("Санкт-Петербург")
            page.get_by_role("button", name="О сервисе", exact=True).click()
            expect(page.get_by_role("heading", name="Анна, поехали?")).to_be_visible()
            page.get_by_role("button", name="Открыть профиль из раздела о сервисе", exact=True).click()
            expect(panel.get_by_label("Дальность подбора городов", exact=True)).to_have_value("350")
            expect(panel.get_by_label("Предпочтительный транспорт", exact=True)).to_have_value("bus")
            panel.get_by_label("Предпочтительный транспорт", exact=True).select_option("car")
            expect(panel.get_by_role("button", name="Сохранить настройки", exact=True)).to_be_visible()
            panel.get_by_role("button", name="Сохранить настройки", exact=True).click()
            expect(panel.get_by_role("button", name="Настройки сохранены", exact=True)).to_be_visible()
            assert page.evaluate("JSON.parse(sessionStorage.getItem('nearby:v2:max:42:draft')).has_car")
            page.get_by_role("button", name="Назад из профиля", exact=True).click()
            expect(page.locator('[data-ui="about-page"]')).to_be_visible()
            page.goto(f"{args.base_url.rstrip('/')}/?WebAppStartParam=trip_{'a' * 32}")
            page.get_by_role("tab", name="Дорога", exact=True).click()
            expect(page.locator('[data-ui="moscow-ticket-note"]')).to_be_visible()
            expect(page.locator('[data-ui="weather-card"]').get_by_text("Open-Meteo")).to_have_count(0)
            assert page.locator('[data-ui="weather-card"]').evaluate("""el => {
                const advice = el.querySelector('[data-ui=weather-advice]');
                return Math.abs(el.getBoundingClientRect().bottom - advice.getBoundingClientRect().bottom -
                    parseFloat(getComputedStyle(el).paddingBottom)) < 1;
            }""")
            for label, from_city, to_city, day in [("Расписание туда", "Москва", plan["destination"]["title"], "2026-09-30"),
                                                 ("Расписание обратно", plan["destination"]["title"], "Москва", "2026-10-01")]:
                page.get_by_role("button", name=label, exact=True).click()
                url = page.evaluate("WebApp.calls.at(-1)")
                query = parse_qs(urlparse(url).query)
                assert query == {"fromName": [from_city], "toName": [to_city], "when": [day]}
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            page.screenshot(path=str(screenshots / f"transport-header-{args.browser}-{width}.png"), full_page=True)
            plan["request"]["origin"] = "Санкт-Петербург"
            page.reload()
            page.get_by_role("tab", name="Дорога", exact=True).click()
            expect(page.locator('[data-ui="moscow-ticket-note"]')).to_have_count(0)
            assert not errors, errors
            context.close()
        browser.close()
    print(f"Profile, categories, schedule links and weather spacing passed ({args.browser}, 320/390/1360 px).")


if __name__ == "__main__":
    main()
