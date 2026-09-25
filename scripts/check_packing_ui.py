"""Check checklist restore, save and errors in a browser; API responses are mocked."""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import expect, sync_playwright

from scripts.check_ui import BRIDGE
from src.sample import sample_trip


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:18092")
    args = parser.parse_args()
    plan = sample_trip().model_dump(mode="json")
    plan["packed_items"] = [1]
    fail = False
    hold = False
    held = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        context = browser.new_context(viewport={"width": 390, "height": 844})
        context.add_init_script('localStorage.setItem("nearby:onboarding:v2", "true")')
        context.route("https://st.max.ru/**", lambda r: r.fulfill(
            content_type="application/javascript", body=BRIDGE))
        context.route("**/api/v1/auth/me", lambda r: r.fulfill(
            json={"mode": "max", "user": {"id": 42, "first_name": "Тест"}}))
        context.route("**/api/v1/trips", lambda r: r.fulfill(json={
            "items": [{"id": plan["id"], "title": plan["title"],
                       "start_date": plan["request"]["start_date"],
                       "travelers": 2, "estimated_total_rub": 10000}],
            "total": 1, "next_cursor": None}))
        context.route(f"**/api/v1/trips/{plan['id']}", lambda r: r.fulfill(json=plan))

        def respond(route):
            assert route.request.method == "PATCH"
            assert route.request.headers["x-max-init-data"] == "test-launch-data"
            if fail:
                route.fulfill(status=503, json={"error": "Не удалось сохранить чеклист"})
                return
            data = route.request.post_data_json
            checked = set(plan["packed_items"])
            if data["checked"]:
                checked.add(data["item_index"])
            else:
                checked.discard(data["item_index"])
            plan["packed_items"] = sorted(checked)
            route.fulfill(json=plan)

        def packing(route):
            if hold:
                held.append(route)
            else:
                respond(route)

        def release():
            deadline = time.monotonic() + 5
            while not held and time.monotonic() < deadline:
                page.wait_for_timeout(10)
            assert held, "Background write did not arrive"
            respond(held.pop(0))

        context.route(f"**/api/v1/trips/{plan['id']}/packing", packing)
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        def open_trip():
            page.get_by_role("button", name="Мои поездки", exact=True).click()
            page.get_by_role("button", name=plan["title"], exact=False).click()

        page.goto(args.base_url)
        open_trip()
        checks = page.locator('[data-ui~="packing-list"] input')
        expect(checks.nth(1)).to_be_checked()
        labels = page.locator('[data-ui~="packing-list"] label')
        hold = True
        labels.nth(0).click()
        expect(checks.nth(0)).to_be_checked()
        expect(checks.nth(0)).to_be_enabled()
        assert plan["packed_items"] == [1]  # Server has not replied yet.
        labels.nth(0).click()
        labels.nth(2).click()
        expect(checks.nth(0)).not_to_be_checked()
        expect(checks.nth(2)).to_be_checked()
        release()  # A stale response for the first click must not undo newer clicks.
        expect(checks.nth(0)).not_to_be_checked()
        expect(checks.nth(2)).to_be_checked()
        release()
        release()
        assert plan["packed_items"] == [1, 2]
        hold = False
        page.reload()
        open_trip()
        expect(checks.nth(0)).not_to_be_checked()
        expect(checks.nth(2)).to_be_checked()
        with page.expect_response("**/packing"):
            labels.nth(0).click()
        expect(checks.nth(0)).to_be_checked()
        page.reload()
        open_trip()
        expect(checks.nth(0)).to_be_checked()
        expect(checks.nth(1)).to_be_checked()
        with page.expect_response("**/packing"):
            labels.nth(0).click()
        expect(checks.nth(0)).not_to_be_checked()
        fail = True
        page.locator('[data-ui~="packing-list"] label').nth(0).click()
        expect(page.get_by_text("Не удалось сохранить чеклист", exact=True)).to_be_visible()
        expect(checks.nth(0)).not_to_be_checked()
        assert not errors, errors
        browser.close()
    print("Checklist UI: immediate toggles, rapid clicks, delayed responses, reload and rollback passed")


if __name__ == "__main__":
    main()
