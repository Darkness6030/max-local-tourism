"""React browser regression. Generation and MAX Bridge are mocked; no messages sent."""

import argparse
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import expect, sync_playwright

from src.sample import sample_trip

BRIDGE = """window.WebApp = {
  initData: 'test-launch-data', calls: [],
  ready() { this.calls.push('ready'); },
  BackButton: { show() {}, hide() {}, onClick(fn) { this.callback = fn; },
    offClick(fn) { if (this.callback === fn) this.callback = null; } },
  enableClosingConfirmation() {}, disableClosingConfirmation() {},
  shareMaxContent(data) { this.calls.push(data); return Promise.resolve(); },
  openLink(url) { this.calls.push(url); }
};"""


def mock_profile(context, completed=False):
    profile = {"onboarding_completed": completed}

    def complete(route):
        assert route.request.method == "PUT"
        profile["onboarding_completed"] = True
        route.fulfill(json=profile)

    context.route("**/api/v1/profile", lambda r: r.fulfill(json=profile))
    context.route("**/api/v1/profile/onboarding", complete)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8001")
    parser.add_argument("--browser", default="chrome")
    parser.add_argument("--height", type=int, default=844)
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    sample = {"plan": sample_trip().model_dump(mode="json")}
    plan = copy.deepcopy(sample["plan"])
    plan["title"] = 'Маршрут <img src=x onerror="window.injected=true">'
    plan["summary"] = "GigaChat подготовил AI-программу."
    plan["share_text"] = "GigaChat: AI-программа. https://example.com/AI"
    train = {
        "transport_type": "suburban", "departure": "2026-09-27T09:00:00+03:00",
        "arrival": "2026-09-27T11:00:00+03:00", "duration_minutes": 120,
        "from_station": "Москва", "to_station": "Коломна", "has_transfers": False,
        "price_rub": 450, "buy_url": "https://rasp.yandex.ru/",
    }
    plan["transport"] = {"outbound": [train, {**train, "transport_type": "bus"}], "return_trip": []}
    screenshots = Path("tmp/ui-check")
    screenshots.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel=None if args.browser == "chromium" else args.browser
        )
        context = browser.new_context(viewport={"width": 390, "height": args.height})
        mock_profile(context)
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
        context.route("**/api/v1/examples/trip-plan", lambda r: r.fulfill(json=sample))
        context.route("**/api/v1/cities/validate?*", lambda r: r.fulfill(json={"city": {"title": "Коломна"}, "distance_km": 100}))
        context.route("**/api/v1/trips/*/share", lambda r: r.fulfill(json={
            "text": plan["share_text"] + "\nhttps://max.ru/test_bot?startapp=trip_" + "a" * 32,
        }))
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))

        def screenshot(name):
            page.wait_for_timeout(800)
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(100)
            assert not page.evaluate(
                "document.documentElement.scrollWidth > innerWidth"
            ), name
            page.screenshot(path=str(screenshots / f"{name}.png"), full_page=True)

        submissions, polls = [], []

        def submit(route):
            submissions.append(route.request.post_data_json)
            route.fulfill(status=202, json={"id": "test-job", "status": "queued"})

        def status(route):
            polls.append(True)
            if len(polls) == 1:
                route.fulfill(status=503, json={"error": "Тестовый обрыв соединения"})
            else:
                route.fulfill(
                    json={
                        "id": "test-job",
                        "status": "succeeded",
                        "progress": 100,
                        "message": "Готово",
                        "events": [],
                        "result": plan,
                        "error": None,
                    }
                )

        def history(route):
            items = []
            if polls:
                items = [{"id": plan["id"], "title": plan["title"],
                          "start_date": plan["request"]["start_date"],
                          "travelers": plan["request"]["travelers"],
                          "estimated_total_rub": plan["budget"]["estimated_total_rub"]}]
            route.fulfill(json={"items": items, "total": len(items), "next_cursor": None})

        context.route("**/api/v1/trips", history)
        def packing(route):
            update = route.request.post_data_json
            packed = set(plan["packed_items"])
            if update["checked"]:
                packed.add(update["item_index"])
            else:
                packed.discard(update["item_index"])
            plan["packed_items"] = sorted(packed)
            route.fulfill(json=plan)

        context.route(f"**/api/v1/trips/{plan['id']}/packing", packing)
        context.route(f"**/api/v1/trips/{plan['id']}", lambda r: r.fulfill(json=plan))
        context.route("**/api/v1/trips/jobs", submit)
        context.route("**/api/v1/trips/jobs/test-job", status)
        page.goto(base, wait_until="networkidle")
        expect(page.get_by_role("heading", name="Большие впечатления.")).to_be_visible()
        screenshot("onboarding-mobile")
        page.get_by_role("button", name="Дальше", exact=True).click()
        expect(page.get_by_role("heading", name="Ваше настроение.")).to_be_visible()
        screenshot("onboarding-preferences-mobile")
        page.get_by_role("button", name="Дальше", exact=True).click()
        expect(page.get_by_role("heading", name="Меньше планировать.")).to_be_visible()
        page.evaluate("""() => {
            window.welcomeFrames = [];
            const until = performance.now() + 2000;
            function sample() {
                const onboard = document.querySelector('[data-ui~=onboarding]')?.parentElement;
                const home = document.querySelector('[data-ui~=screen-home]');
                const content = document.querySelector('[data-ui~=home-page]');
                window.welcomeFrames.push({t: performance.now(),
                    exit: onboard ? Number(getComputedStyle(onboard).opacity) : null,
                    enter: home ? Number(getComputedStyle(home).opacity) : null,
                    transform: content ? getComputedStyle(content).transform : 'none'});
                if (performance.now() < until) requestAnimationFrame(sample);
            }
            requestAnimationFrame(sample);
        }""")
        page.get_by_role("button", name="Начать путешествие").click()
        expect(page.get_by_role("button", name="Спланировать поездку")).to_be_visible()
        page.wait_for_timeout(750)
        assert page.evaluate("""() => {
            const entered = window.welcomeFrames.filter(f => f.enter !== null);
            return entered.length > 0 && entered.every(f => f.exit === null) &&
                entered.at(-1).enter === 1;
        }"""), "Home should replace onboarding immediately, without an exit animation."
        screenshot("home-mobile")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        footer_gap = page.evaluate("""() => {
            const footer = document.querySelector('[data-ui~=home-footer]').getBoundingClientRect();
            const nav = document.querySelector('[data-ui~=bottom-nav]').getBoundingClientRect();
            return nav.top - footer.bottom;
        }""")
        assert 8 <= footer_gap <= 24, footer_gap
        page.get_by_role("button", name="Мои поездки", exact=True).click()
        expect(
            page.get_by_role("heading", name="Ваши открытия ещё впереди")
        ).to_be_visible()
        page.get_by_role("button", name="Главная", exact=True).click()
        plan_button = page.get_by_role("button", name="Спланировать поездку")
        plan_button.hover()
        page.wait_for_timeout(250)
        hover_style = plan_button.evaluate(
            "el => ({color: getComputedStyle(el).color, background: getComputedStyle(el).backgroundColor})"
        )
        assert hover_style == {
            "color": "rgb(48, 73, 215)",
            "background": "rgb(238, 242, 255)",
        }, hover_style
        # Record every outgoing animation frame: changing the destination screen
        # must not apply its edge-to-edge layout to the still-visible home screen.
        page.evaluate("""() => {
            window.homeInsets = [];
            window.screenFadeFrames = [];
            const until = performance.now() + 700;
            function sample() {
                const heading = document.querySelector('[data-ui~=home-heading]');
                if (heading) window.homeInsets.push(heading.getBoundingClientRect().left);
                const next = document.querySelector('[data-ui~=screen-wizard]');
                if (next) window.screenFadeFrames.push({t: performance.now(), opacity: Number(getComputedStyle(next).opacity)});
                if (performance.now() < until) requestAnimationFrame(sample);
            }
            requestAnimationFrame(sample);
        }""")
        plan_button.click()
        page.get_by_role("button", name="Уже знаю куда").click()
        page.wait_for_timeout(400)
        assert page.evaluate(
            "window.homeInsets.every(x => x >= 23)"
        )
        assert page.evaluate("""() => {
            const fading = window.screenFadeFrames.filter(f => f.opacity > 0.05 && f.opacity < 0.95);
            return window.screenFadeFrames.length > 0 &&
                (!fading.length || fading.at(-1).t - fading[0].t < 200);
        }"""), "Screen entry should finish promptly without waiting for the old screen."
        page.locator("#next-step").click()
        expect(page.get_by_role("alert")).to_contain_text("Введите город")
        page.locator("input[name=destination]").fill("Коломна")
        screenshot("wizard-direction-mobile")
        page.locator("#next-step").click()
        date = page.locator("input[name=start_date]")
        expect(date).to_be_visible()
        original_date = date.input_value()
        date.fill("")
        expect(page.get_by_text("Выберите дату", exact=True)).to_be_visible()
        date.fill(original_date)
        screenshot("wizard-dates-mobile")
        page.locator("#next-step").click()
        page.get_by_role("button", name="С семьёй").click()
        page.locator("input[name=children_ages]").fill("5, 12")
        page.locator("#next-step").click()
        expect(page.get_by_role("alert")).to_contain_text("взрослого")
        page.get_by_role("button", name="Увеличить: Число путешественников").click()
        page.get_by_role("button", name="Увеличить: Число путешественников").click()
        expect(page.get_by_label("Число путешественников", exact=True)).to_have_text(
            "4"
        )
        page.reload(wait_until="networkidle")
        page.get_by_role("button", name="Спланировать поездку").click()
        expect(page.locator("input[name=children_ages]")).to_have_value("5, 12")
        screenshot("wizard-family-mobile")
        page.locator("#next-step").click()
        expect(
            page.get_by_role("heading", name="Что делает день вашим?")
        ).to_be_visible()
        page.evaluate("window.WebApp.BackButton.callback()")
        expect(page.locator("input[name=children_ages]")).to_have_value("5, 12")
        page.locator("#next-step").click()
        page.get_by_role("button", name="Природа Леса и тишина").click()
        screenshot("wizard-interests-mobile")
        page.locator("#next-step").click()
        expect(page.locator("#generate")).to_be_visible()
        assert not submissions
        screenshot("wizard-budget-mobile")
        page.locator("#generate").click()
        expect(page.locator("#retry-poll")).to_be_visible()
        screenshot("loading-mobile")
        page.locator("#retry-poll").click()
        expect(page.locator("#result-title")).to_have_text(plan["title"])
        expect(page.locator("[data-ui~=result-hero] > p")).to_have_text(
            "ИИ подготовил ИИ-программу."
        )
        page.locator("#share-trip").click()
        assert page.evaluate(
            "window.WebApp.calls.some(x => x.text?.startsWith('ИИ: ИИ-программа. https://example.com/AI') && x.text.includes('?startapp=trip_'))"
        )
        assert len(submissions) == 1
        assert submissions[0]["children_ages"] == [5, 12]
        assert submissions[0]["travelers"] == 4
        assert submissions[0]["destination"] == "Коломна"
        assert "Природа" in submissions[0]["preferences"]
        assert not page.evaluate("Boolean(window.injected)")
        expect(page.locator("#result-title img")).to_have_count(0)
        expect(page.locator("#demo-notice")).to_have_count(0)
        page.get_by_role("button", name="Изменить пожелания").click()
        expect(page.locator("input[name=destination]")).to_have_value("Коломна")
        for _ in range(4):
            page.locator("#next-step").click()
            page.wait_for_timeout(450)
        context.unroute("**/api/v1/trips/jobs")
        context.route(
            "**/api/v1/trips/jobs",
            lambda r: r.fulfill(
                status=422,
                json={"detail": [{"msg": "Value error, тестовая ошибка даты"}]},
            ),
        )
        page.locator("#generate").click()
        expect(page.get_by_role("alert")).to_contain_text("тестовая ошибка даты")
        expect(page.locator("#generate")).to_be_enabled()
        page.get_by_role("button", name="Закрыть анкету").click()
        page.get_by_role("button", name="Мои поездки", exact=True).click()
        page.locator("[data-ui~=saved-trip]").click()
        screenshot("result-mobile")
        page.get_by_role("checkbox").first.check()
        page.get_by_role("tab", name="Бюджет").click()
        expect(page.locator("#budget")).to_contain_text("7 600")
        screenshot("result-budget-mobile")
        page.get_by_role("tab", name="Дорога").click()
        expect(page.get_by_role("img", name="Автобус", exact=True)).to_be_visible()
        assert page.get_by_role("img", name="Электричка", exact=True).count() >= 1
        page.locator("#map-link").click()
        assert page.evaluate(
            "window.WebApp.calls.some(x => typeof x === 'string' && x.startsWith('https://yandex.ru/maps/'))"
        )
        page.locator("#share-trip").click()
        assert page.evaluate("window.WebApp.calls.some(x => x.text?.startsWith('ИИ:'))")
        page.locator("#copy-trip").click()
        expect(page.locator("[data-ui~=share-feedback]")).to_be_visible()
        page.get_by_role("tab", name="Программа").click()
        expect(page.get_by_role("checkbox").first).to_be_checked()
        page.set_viewport_size({"width": 320, "height": 650})
        screenshot("result-narrow")
        page.get_by_role("button", name="На главную", exact=True).click()
        screenshot("home-narrow")
        page.get_by_role("button", name="О сервисе", exact=True).click()
        page.get_by_role("button", name="Посмотреть знакомство ещё раз").click()
        screenshot("onboarding-narrow")
        page.get_by_role("button", name="Пропустить знакомство").click()
        page.set_viewport_size({"width": 1360, "height": args.height})
        page.get_by_role("button", name="Главная", exact=True).click()
        screenshot("home-desktop")
        page.get_by_role("button", name="Мои поездки", exact=True).click()
        page.locator("[data-ui~=saved-trip]").click()
        expect(page.locator("#result-title")).to_be_visible()
        screenshot("result-desktop")
        page.get_by_role("button", name="Изменить пожелания").click()
        screenshot("wizard-desktop")
        page.emulate_media(reduced_motion="reduce")
        page.locator("#next-step").click()
        expect(page.locator("input[name=start_date]")).to_be_visible()
        assert not errors, errors
        browser.close()
    print(
        "UI passed: onboarding, 5 steps, 320/390/1360px, draft, validation, single job/retry, tabs, copy, mock MAX Bridge, XSS, reduced motion. No messages or live generation."
    )


if __name__ == "__main__":
    main()
