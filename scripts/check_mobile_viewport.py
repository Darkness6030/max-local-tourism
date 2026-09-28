"""Mobile focus, keyboard and navigation regression; all API/Bridge calls are mocked.

VisualViewport resizing is simulated. This does not replace a device check in MAX.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import expect, sync_playwright

from scripts.check_ui import BRIDGE, mock_profile
from src.cities import get_city_catalog
from src.sample import sample_trip


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:5173")
    parser.add_argument("--browser", choices=["chrome", "webkit"], default="chrome")
    parser.add_argument("--max-platform", choices=["ios", "android", "web"], default="web")
    parser.add_argument("--safe-bottom", type=int, default=0)
    args = parser.parse_args()
    if args.safe_bottom and args.browser != "chrome":
        parser.error("Nonzero safe-area emulation requires Chrome/CDP")
    screenshots = Path("tmp/ui-check")
    screenshots.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.webkit.launch() if args.browser == "webkit" else p.chromium.launch(channel="chrome")
        for width in (320, 390):
            context = browser.new_context(
                viewport={"width": width, "height": 844}, is_mobile=True,
                has_touch=True, reduced_motion="no-preference", locale="en-US",
            )
            mock_profile(context, completed=True)
            context.route("https://st.max.ru/**", lambda r: r.fulfill(
                content_type="application/javascript",
                body=BRIDGE + f"window.WebApp.platform = '{args.max_platform}';",
            ))
            context.route("**/api/v1/auth/me", lambda r: r.fulfill(
                json={"mode": "max", "user": {"id": 42, "first_name": "Анна"}},
            ))
            context.route("**/api/v1/app-config", lambda r: r.fulfill(json={
                "today": "2026-09-27", "default_date": "2026-09-28",
                "last_trip_date": "2026-10-10", "max_days": 3,
                **get_city_catalog().public(), "bot_url": None,
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
            if args.browser == "chrome":
                context.new_cdp_session(page).send("Emulation.setSafeAreaInsetsOverride", {
                    "insets": {"bottom": args.safe_bottom},
                })
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
                base_padding = {
                    "[data-ui~=bottom-nav]": 6,
                    "[data-ui~=preset-actions]": 10,
                }.get(selector, 12)
                inset = args.safe_bottom / 2 if args.max_platform == "ios" else args.safe_bottom
                assert bar.evaluate("el => parseFloat(getComputedStyle(el).paddingBottom)") == max(base_padding, inset), selector

            check_bar("[data-ui~=bottom-nav]")
            page.get_by_role("button", name="Открыть маршрут: Коломна", exact=True).click()
            check_bar("[data-ui~=preset-actions]")
            page.get_by_role("button", name="На главную", exact=True).click()
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
            expect(destination).not_to_be_focused()

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
                inset = args.safe_bottom / 2 if args.max_platform == "ios" else args.safe_bottom
                assert page.locator("[data-ui~=wizard-actions]").evaluate(
                    "el => parseFloat(getComputedStyle(el).paddingBottom)"
                ) == max(12, inset)
                for control in page.locator("[data-ui~=step-content] input, [data-ui~=step-content] select, [data-ui~=step-content] textarea").all():
                    if control.is_visible():
                        assert control.evaluate("el => parseFloat(getComputedStyle(el).fontSize) >= 16")
                if step == 3:
                    keyboard_check(page.locator("textarea[name=preferences]"))
                if step == 1:
                    date = page.locator("input[name=start_date]")
                    initial_date = date.input_value()
                    initial_height = date.bounding_box()["height"]
                    date.fill("")
                    assert date.bounding_box()["height"] == initial_height
                    date.fill(initial_date)
                    assert date.evaluate("""el => {
                        const s = getComputedStyle(el);
                        const r = el.getBoundingClientRect();
                        const icon = el.parentElement.querySelector('svg').getBoundingClientRect();
                        return ['flex', 'inline-flex'].includes(s.display) && s.alignItems === 'center' &&
                            s.paddingTop === '0px' && s.paddingBottom === '0px' &&
                            Math.abs(r.y + r.height / 2 - icon.y - icon.height / 2) < 1;
                    }"""), "Date text must use WebKit's centered flex layout"
                    page.locator("[data-ui~=date-input]").screenshot(
                        path=str(screenshots / f"date-{args.browser}-{width}.png")
                    )
                if step == 4:
                    page.locator("summary").filter(has_text="Время в дороге").click()
                    for name, value in (("departure_after", "09:45"), ("return_after", "19:30")):
                        field = page.locator(f"input[name={name}]")
                        field.fill(value)
                        field.blur()
                        expect(field).to_have_value(value)
                        field.evaluate("el => el.scrollIntoView({block: 'center', behavior: 'instant'})")
                        page.wait_for_timeout(100)
                        metrics = field.evaluate("""el => {
                            const s = getComputedStyle(el);
                            const frame = el.closest('[data-ui~=time-input]');
                            const r = el.getBoundingClientRect();
                            const box = frame.getBoundingClientRect();
                            return {padding: s.padding, margin: s.margin, border: s.borderWidth,
                                contained: r.left >= box.left && r.right <= box.right &&
                                    r.top >= box.top && r.bottom <= box.bottom,
                                hit: document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2) === el};
                        }""")
                        assert metrics == {
                            "padding": "0px", "margin": "0px", "border": "0px",
                            "contained": True, "hit": True,
                        }, metrics
                    assert page.locator("[data-ui~=fields-pair]").evaluate("""el => {
                        const pair = el.getBoundingClientRect();
                        const fields = [...el.querySelectorAll('[data-ui~=time-input]')].map(x => x.getBoundingClientRect());
                        return fields.length === 2 && fields[0].left >= pair.left &&
                            fields[0].right + 11 <= fields[1].left && fields[1].right <= pair.right + 1 &&
                            pair.right <= innerWidth && fields.every(r => r.width > 0 && r.height >= 44);
                    }"""), "Time inputs must fit in separate columns"
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                    page.locator("[data-ui~=fields-pair]").screenshot(
                        path=str(screenshots / f"times-{args.browser}-{width}.png")
                    )
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
            print(f"Mobile viewport passed: {args.browser}, {width}px, MAX {args.max_platform}, safe bottom {args.safe_bottom}px", flush=True)
            context.close()
        browser.close()


if __name__ == "__main__":
    main()
