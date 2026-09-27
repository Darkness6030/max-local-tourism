"""Mobile focus, keyboard and navigation regression; all API/Bridge calls are mocked.

VisualViewport resizing is simulated. This does not replace a device check in MAX.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import expect, sync_playwright

from scripts.check_ui import BRIDGE, mock_profile
from src.sample import sample_trip


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:5173")
    parser.add_argument("--browser", choices=["chrome", "webkit"], default="chrome")
    args = parser.parse_args()
    with sync_playwright() as p:
        browser = p.webkit.launch() if args.browser == "webkit" else p.chromium.launch(channel="chrome")
        for width in (320, 390):
            context = browser.new_context(
                viewport={"width": width, "height": 844}, is_mobile=True,
                has_touch=True, reduced_motion="no-preference",
            )
            mock_profile(context, completed=True)
            context.route("https://st.max.ru/**", lambda r: r.fulfill(
                content_type="application/javascript", body=BRIDGE,
            ))
            context.route("**/api/v1/auth/me", lambda r: r.fulfill(
                json={"mode": "max", "user": {"id": 42, "first_name": "Анна"}},
            ))
            context.route("**/api/v1/app-config", lambda r: r.fulfill(json={
                "today": "2026-09-27", "default_date": "2026-09-28",
                "last_trip_date": "2026-10-10", "max_days": 3,
                "origins": ["Москва", "Санкт-Петербург"], "bot_url": None,
            }))
            context.route("**/api/v1/trips", lambda r: r.fulfill(
                json={"items": [], "total": 0, "next_cursor": None},
            ))
            context.route("**/api/v1/cities/validate?*", lambda r: r.fulfill(
                json={"city": {"title": "Коломна"}, "distance_km": 100},
            ))
            context.route("**/api/v1/trips/jobs", lambda r: r.fulfill(
                status=202, json={"id": "mobile-check", "status": "queued"},
            ))
            context.route("**/api/v1/trips/jobs/mobile-check", lambda r: r.fulfill(json={
                "id": "mobile-check", "status": "succeeded", "progress": 100,
                "message": "Готово", "events": [], "error": None,
                "result": sample_trip().model_dump(mode="json"),
            }))
            context.route("**/api/v1/trips/*/share", lambda r: r.fulfill(json={"text": "Тест"}))
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda error, errors=errors: errors.append(str(error)))
            page.goto(args.base_url, wait_until="networkidle")

            def check_bar(selector, page=page):
                bar = page.locator(selector)
                expect(bar).to_be_visible()
                assert bar.evaluate("""el => {
                    const r = el.getBoundingClientRect();
                    return Math.abs(r.bottom - innerHeight) < 1 &&
                        getComputedStyle(el).backgroundColor === getComputedStyle(document.body).backgroundColor;
                }"""), selector

            check_bar("[data-ui~=bottom-nav]")
            # A click must replace the screen within the next two render frames.
            page.get_by_role("button", name="Спланировать поездку").evaluate("""async el => {
                el.click();
                await new Promise(requestAnimationFrame);
                await new Promise(requestAnimationFrame);
                if (!document.querySelector('[data-ui~=screen-wizard]') ||
                    document.querySelector('[data-ui~=screen-home]')) throw Error('Delayed navigation');
            }""")
            page.get_by_role("button", name="Уже знаю куда").click()
            destination = page.locator("input[name=destination]")
            expect(destination).to_be_focused()

            def keyboard_check(field, page=page):
                assert field.evaluate("el => parseFloat(getComputedStyle(el).fontSize) >= 16")
                field.focus()
                # iOS-style: layout stays tall while the keyboard covers its bottom.
                page.evaluate("""() => {
                    Object.defineProperty(visualViewport, 'height', {configurable: true, value: 300});
                    Object.defineProperty(visualViewport, 'offsetTop', {configurable: true, value: 0});
                    visualViewport.dispatchEvent(new Event('resize'));
                }""")
                page.wait_for_timeout(400)
                expect(field).to_be_focused()
                assert field.evaluate("""el => {
                    const r = el.getBoundingClientRect();
                    return r.top >= 11 && r.bottom <= visualViewport.height - 11;
                }"""), field.get_attribute("name")
                assert page.locator("[data-ui~=wizard-actions]").evaluate(
                    "el => getComputedStyle(el).position === 'static'"
                )
                # Keyboard dismissal must restore normal layout, without a gap.
                field.evaluate("el => el.blur()")
                page.evaluate("""() => {
                    delete visualViewport.height;
                    delete visualViewport.offsetTop;
                    visualViewport.dispatchEvent(new Event('resize'));
                }""")
                page.wait_for_timeout(100)
                assert page.evaluate("!document.documentElement.hasAttribute('data-keyboard-open')")
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")

            keyboard_check(destination)
            destination.fill("Коломна")
            for step in range(5):
                expect(page.get_by_label(f"Шаг {step + 1} из 5", exact=True)).to_be_visible()
                for control in page.locator("[data-ui~=step-content] input, [data-ui~=step-content] select, [data-ui~=step-content] textarea").all():
                    if control.is_visible():
                        assert control.evaluate("el => parseFloat(getComputedStyle(el).fontSize) >= 16")
                if step == 3:
                    keyboard_check(page.locator("textarea[name=preferences]"))
                if step < 4:
                    page.locator("#next-step").click()
            page.get_by_role("button", name="Закрыть анкету").click()
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            check_bar("[data-ui~=bottom-nav]")
            page.get_by_role("button", name="Спланировать поездку").click()
            page.locator("#generate").click()
            check_bar("[data-ui~=result-sticky]")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            check_bar("[data-ui~=result-sticky]")
            assert not errors, errors
            print(f"Mobile viewport passed: {args.browser}, {width}px", flush=True)
            context.close()
        browser.close()


if __name__ == "__main__":
    main()
