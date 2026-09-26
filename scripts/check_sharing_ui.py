"""Shared launch and onboarding regression; MAX sending and API are mocked."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from playwright.sync_api import expect, sync_playwright

from scripts.check_ui import BRIDGE
from src.sample import sample_trip


def main():
    plan = sample_trip().model_dump(mode="json")
    token = "a" * 32
    link = f"https://max.ru/test_bot?startapp=trip_{token}"
    shared_text = plan["share_text"] + "\n\nСохранить и открыть маршрут:\n" + link
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        for completed in [False, True]:
            context = browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
            context.route("**/static/**", lambda r: r.fulfill(
                path=str(Path("src/static") / r.request.url.split("/static/", 1)[1])))
            context.route("https://st.max.ru/**", lambda r: r.fulfill(
                content_type="application/javascript", body=BRIDGE))
            context.route("**/api/v1/auth/me", lambda r: r.fulfill(
                json={"mode": "max", "user": {"id": 43, "first_name": "Анна"}}))
            context.route("**/api/v1/app-config", lambda r: r.fulfill(json={
                "today": "2026-09-26", "default_date": "2026-09-27", "last_trip_date": "2026-10-10",
                "max_days": 3, "origins": ["Москва", "Санкт-Петербург"], "bot_url": "https://max.ru/test_bot?startapp",
            }))
            context.route("**/api/v1/profile", lambda r, *, done=completed: r.fulfill(json={"onboarding_completed": done}))
            context.route("**/api/v1/profile/onboarding", lambda r: r.fulfill(json={"onboarding_completed": True}))
            imports = []

            def import_trip(route, *, calls=imports):
                assert route.request.method == "POST"
                calls.append(route.request.url)
                route.fulfill(json=plan)

            context.route(f"**/api/v1/shared-trips/{token}/import", import_trip)
            preparations = []

            def prepare_share(route, *, attempts=preparations, fail_first=completed):
                assert route.request.method == "POST"
                attempts.append(True)
                if fail_first and len(attempts) == 1:
                    route.fulfill(status=503, json={"error": "Temporary failure"})
                else:
                    route.fulfill(json={"text": shared_text, "url": link})

            context.route(f"**/api/v1/trips/{plan['id']}/share", prepare_share)
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda e, captured=errors: captured.append(str(e)))
            await_url = f"http://127.0.0.1:8769/?WebAppStartParam=trip_{token}"
            page.goto(await_url)
            if not completed:
                expect(page.locator('[data-ui="onboarding"]')).to_be_visible()
                page.get_by_role("button", name="Пропустить знакомство").click()
            expect(page.locator('[data-ui="result-page"]')).to_be_visible()
            assert len(imports) == 1
            if completed:
                expect(page.locator("#share-trip")).to_have_text("Повторить подготовку")
                page.locator("#share-trip").click()
            expect(page.locator("#share-trip")).to_have_text("Позвать с собой")
            expect(page.locator("#share-trip")).to_be_enabled()
            assert len(preparations) == (2 if completed else 1)
            before_click = len(preparations)
            assert page.evaluate("window.WebApp.calls.filter(x => x && x.text).length") == 0
            page.locator("#share-trip").click()
            expect(page.get_by_role("dialog")).to_have_count(0)
            assert len(preparations) == before_click
            assert page.evaluate("window.WebApp.calls.filter(x => x && x.text).at(-1).text") == shared_text
            assert not errors, errors
            context.close()
        browser.close()
    print("Shared launch, onboarding and MAX share text passed")


if __name__ == "__main__":
    main()
