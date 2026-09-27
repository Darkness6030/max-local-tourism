"""Shared launch and onboarding regression; MAX sending and API are mocked."""

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from playwright.sync_api import expect, sync_playwright

from scripts.check_ui import BRIDGE
from src.sample import sample_trip


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8769")
    parser.add_argument("--browser", choices=["chrome", "webkit"], default="chrome")
    args = parser.parse_args()
    plan = sample_trip().model_dump(mode="json")
    token = "a" * 32
    link = f"https://max.ru/test_bot?startapp=trip_{token}"
    shared_text = plan["share_text"] + "\n\nСохранить и открыть маршрут:\n" + link
    with sync_playwright() as p:
        browser = p.webkit.launch() if args.browser == "webkit" else p.chromium.launch(channel="chrome")
        for mode in ["max-new", "max-retry", "ios", "ios-reject", "ios-throw", "ios-hang",
                     "ios-cancel", "ios-error-response", "ios-no-native", "ios-no-initdata",
                     "ios-no-deeplink", "ios-deeplink-throw", "ios-string", "ios-no-max", "ios-no-url", "ios-no-methods", "ios-late", "browser"]:
            completed = mode != "max-new"
            context = browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce",
                                          is_mobile=True, has_touch=True)
            if args.base_url == "http://127.0.0.1:8769":
                context.route("**/static/**", lambda r: r.fulfill(
                    path=str(Path("src/static") / r.request.url.split("/static/", 1)[1])))
            bridge_script = BRIDGE + """
                window.shareCalls = [];
                const record = (method, data) => {
                    if (!navigator.userActivation.isActive) throw Error('Lost user activation');
                    window.shareCalls.push({method, ...data});
                };
                const response = () => {
                    if (mode === 'ios-throw') throw Error('Unavailable');
                    if (mode === 'ios-string') return Promise.reject('native_unavailable');
                    if (mode === 'ios-reject') return Promise.reject({error: {
                        code: 'client.web_app_max_share.not_supported',
                        message: 'Failed https://max.ru/test_bot?startapp=trip_private',
                        initData: 'PRIVATE_DATA'
                    }});
                    if (mode === 'ios-error-response') return Promise.resolve({error: {code: 'not_supported'}});
                    if (mode === 'ios-hang') return new Promise(() => {});
                    if (mode === 'ios-cancel') return Promise.reject(new DOMException('Cancelled', 'AbortError'));
                    if (mode === 'ios-late') return new Promise((_, reject) => {
                        window.rejectShare = () => reject({error: {code: 'late_error'}});
                    });
                    return Promise.resolve();
                };
                window.WebApp.shareMaxContent = function(data) { record('max', data); return response(); };
                window.WebApp.openMaxLink = function(url) {
                    record('deeplink', {url});
                    if (mode === 'ios-deeplink-throw') throw Error('Deep link unavailable');
                };
                window.WebApp.version = '26.20.0';
                Object.defineProperty(navigator, 'share', { configurable: true,
                    value(data) { record('browser', data); return Promise.resolve(); } });
            """
            bridge_script += f"const mode = {json.dumps(mode)};"
            bridge_script += """
                if (mode.startsWith('ios')) {
                    window.WebApp.platform = 'ios';
                    window.WebApp.shareContent = function(data) {
                        record('native', data);
                        return response();
                    };
                }
                if (mode === 'ios-no-native') delete window.WebApp.shareContent;
                if (mode === 'ios-no-initdata') window.WebApp.initData = '';
                if (mode === 'ios-no-deeplink') delete window.WebApp.openMaxLink;
                if (mode === 'ios-no-max') delete window.WebApp.shareMaxContent;
                if (mode === 'ios-no-methods') {
                    delete window.WebApp;
                    Object.defineProperty(navigator, 'share', { configurable: true, value: undefined });
                }
                if (mode === 'browser') delete window.WebApp;
            """
            context.route("https://st.max.ru/**", lambda r, *, script=bridge_script: r.fulfill(
                content_type="application/javascript", body=script))
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

            def prepare_share(route, *, attempts=preparations, fail_first=completed, variant=mode):
                assert route.request.method == "POST"
                attempts.append(True)
                if fail_first and len(attempts) == 1:
                    route.fulfill(status=503, json={"error": "Temporary failure"})
                else:
                    route.fulfill(json={"text": shared_text, **({} if variant == "ios-no-url" else {"url": link})})

            context.route(f"**/api/v1/trips/{plan['id']}/share", prepare_share)
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda e, captured=errors: captured.append(str(e)))
            await_url = f"{args.base_url.rstrip('/')}/?WebAppStartParam=trip_{token}#WebAppData=test-launch-data"
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
            assert page.evaluate("window.shareCalls.length") == 0
            page.locator("#share-trip").click()
            expect(page.get_by_role("dialog")).to_have_count(0)
            assert len(preparations) == before_click
            feedback = page.locator("[data-ui~=share-diagnostics]")
            expect(feedback).to_be_visible()
            calls = page.evaluate("window.shareCalls")
            if mode == "ios-no-methods":
                assert calls == []
                expect(feedback).to_contain_text("Отправка недоступна")
            elif mode == "browser":
                assert calls == [{"method": "browser", "text": shared_text}]
            elif mode.startswith("ios") and mode != "ios-no-deeplink":
                assert calls[0]["method"] == "deeplink"
                parsed = urlparse(calls[0]["url"])
                assert parsed.netloc == "max.ru" and parsed.path == "/:share"
                expected_text = shared_text if mode == "ios-no-url" else "Поехали со мной!\n" + link
                assert parse_qs(parsed.query)["text"] == [expected_text]
                expect(feedback).to_contain_text(
                    "Deep link unavailable" if mode == "ios-deeplink-throw" else "SDK не подтверждает открытие")
            elif mode == "ios-no-deeplink":
                assert calls == [{"method": "max", "link": link}]
            else:
                assert calls == [{"method": "max", "text": shared_text}]

            expected_payloads = {
                "link": {"method": "max", "link": link},
                "text-link": {"method": "max", "text": "Поехали со мной!", "link": link},
                "text": {"method": "max", "text": "Поехали со мной!\n" + link},
                "full": {"method": "max", "text": shared_text},
                "native": {"method": "native", "text": shared_text},
                "browser": {"method": "browser", "text": shared_text},
            }
            for method, payload in expected_payloads.items():
                button = page.locator(f'[data-share-method="{method}"]')
                if not button.count():
                    continue
                button.click()
                assert page.evaluate("window.shareCalls.at(-1)") == payload
                if method != "browser":
                    if mode == "ios-reject":
                        expect(feedback).to_contain_text("client.web_app_max_share.not_supported")
                    elif mode == "ios-string":
                        expect(feedback).to_contain_text("native_unavailable")
                    elif mode == "ios-throw":
                        expect(feedback).to_contain_text("Error · Unavailable")
                    elif mode == "ios-error-response":
                        expect(feedback).to_contain_text("not_supported")
                    elif mode == "ios-cancel":
                        expect(feedback).to_contain_text("AbortError")
                    elif mode == "ios-hang" and method == "full":
                        expect(feedback).to_contain_text("нет ответа 8 с", timeout=10000)
                assert len(preparations) == before_click
            if mode == "ios-late":
                # Late SDK failures must update their own row, not erase the next attempt.
                page.evaluate("window.rejectShare()")
                expect(feedback).to_contain_text("late_error")
                expect(feedback.locator('[role="log"] p').first).to_contain_text("без ошибки")
            log_text = feedback.inner_text()
            assert "PRIVATE_DATA" not in log_text and "trip_private" not in log_text
            assert link not in log_text and "test-launch-data" not in log_text
            assert feedback.evaluate("""el => {
                const r = el.getBoundingClientRect();
                return r.top >= 0 && r.bottom <= innerHeight && r.left >= 0 && r.right <= innerWidth;
            }""")
            if mode == "ios-reject":
                page.set_viewport_size({"width": 320, "height": 568})
                assert feedback.evaluate("el => el.scrollWidth <= el.clientWidth")
                screenshot = Path("tmp") / f"share-diagnostics-{args.browser}.png"
                screenshot.parent.mkdir(exist_ok=True)
                page.screenshot(path=str(screenshot))
            feedback.get_by_role("button", name="Закрыть", exact=True).click()
            expect(feedback).to_have_count(0)
            assert not errors, errors
            print(f"Sharing passed: {args.browser}, {mode}", flush=True)
            context.close()
        browser.close()
    print("Shared launch, onboarding and MAX share text passed")


if __name__ == "__main__":
    main()
