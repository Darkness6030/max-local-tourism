"""Check compact MAX windows with a synthetic profile; no generation or messages."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import expect, sync_playwright

from scripts.check_ui import BRIDGE


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:5173")
    args = parser.parse_args()
    screenshots = Path("tmp/ui-check")
    screenshots.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        for width, height in [(w, 633) for w in (320, 390, 450, 600, 800, 1360)] + [
            (390, 844)
        ]:
            context = browser.new_context(
                viewport={"width": width, "height": height}, reduced_motion="reduce"
            )
            context.route(
                "https://st.max.ru/**",
                lambda r: r.fulfill(content_type="application/javascript", body=BRIDGE),
            )
            context.route(
                "**/api/v1/auth/me",
                lambda r: r.fulfill(
                    json={
                        "mode": "max",
                        "user": {
                            "id": 42,
                            "first_name": "Анна",
                            "last_name": "Иванова",
                            "username": "anna",
                            "photo_url": "https://profile.test/avatar.svg",
                        },
                    }
                ),
            )
            context.route(
                "https://profile.test/avatar.svg",
                lambda r: r.fulfill(
                    content_type="image/svg+xml",
                    body='<svg xmlns="http://www.w3.org/2000/svg" width="90" height="60">'
                    '<rect width="90" height="60" fill="#407856"/>'
                    '<circle cx="45" cy="30" r="18" fill="#f6deae"/></svg>',
                ),
            )
            context.route("**/api/v1/trips", lambda r: r.fulfill(json={"items": [], "total": 0, "next_cursor": None}))
            context.route("**/api/v1/cities/validate?*", lambda r: r.fulfill(json={"city": {"title": "Коломна"}, "distance_km": 100}))
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda error, errors=errors: errors.append(str(error)))

            def settled(name, page=page, width=width):
                page.wait_for_timeout(450)
                assert page.evaluate(
                    "document.documentElement.scrollWidth <= innerWidth"
                ), (width, name, "horizontal overflow")
                if width in (450, 1360):
                    page.screenshot(
                        path=str(screenshots / f"compact-{width}-{name}.png")
                    )

            page.goto(args.base_url, wait_until="networkidle")
            expect(
                page.get_by_text("Новые места. Ваш темп. Всё в MAX.", exact=True)
            ).to_have_count(0)
            expect(page.get_by_text("Иллюстрация", exact=True)).to_have_count(0)
            action_tops = []
            for slide in range(3):
                page.get_by_role("button", name=f"Экран знакомства {slide + 1}").click()
                settled(f"onboarding-{slide + 1}")
                metrics = page.evaluate("""() => {
                    const rect = selector => document.querySelector(selector).getBoundingClientRect();
                    const dots = [...document.querySelectorAll('[data-ui~=pagination] span')]
                        .map(el => { const r = el.getBoundingClientRect(); return r.x + r.width / 2; });
                    return {bottom: rect('[data-ui~=onboarding-controls] [data-ui~=primary]').bottom,
                        actionTop: rect('[data-ui~=onboarding-controls] [data-ui~=primary]').top,
                        copyBottom: rect('[data-ui~=onboarding-copy] p').bottom,
                        controlsTop: rect('[data-ui~=onboarding-controls]').top,
                        gaps: [dots[1] - dots[0], dots[2] - dots[1]]};
                }""")
                assert metrics["bottom"] <= height, (width, slide, metrics)
                assert 11 <= height - metrics["bottom"] <= 13, (width, slide, metrics)
                action_tops.append(metrics["actionTop"])
                assert metrics["copyBottom"] <= metrics["controlsTop"], (
                    width,
                    slide,
                    metrics,
                )
                assert abs(metrics["gaps"][0] - metrics["gaps"][1]) < 0.1, metrics
            assert max(action_tops) - min(action_tops) < 1, (width, action_tops)
            page.get_by_role("button", name="Начать путешествие").click()
            expect(page.locator("[data-ui~=app-header] [data-ui~=avatar] img")).to_be_visible()
            settled("home")
            page.get_by_label("Город отправления", exact=True).select_option(
                "Санкт-Петербург"
            )
            expect(page.locator("[data-ui~=origin-pill] > span")).to_have_text("Санкт-Петербург")
            assert page.locator("[data-ui~=origin-pill]").evaluate("""el => {
                const pill = el.getBoundingClientRect();
                const city = el.querySelector('span').getBoundingClientRect();
                const title = document.querySelector('[data-ui~=home-heading] h1').getBoundingClientRect();
                return city.left > pill.left && city.right < pill.right &&
                    (pill.top >= title.bottom || pill.left >= title.right);
            }"""), (width, "city clipped or overlaps heading")
            assert page.locator("[data-ui~=home-side] [data-ui~=section-heading] > span").evaluate("""el => {
                const range = document.createRange(); range.selectNodeContents(el);
                return range.getClientRects().length === 1;
            }"""), (width, "mood subtitle wraps")
            settled("home-city")
            if width <= 700:
                assert page.locator("[data-ui~=bottom-nav]").evaluate("""el => {
                    const r = el.getBoundingClientRect();
                    return Math.abs(r.bottom - innerHeight) < 1 && r.height <= 64
                        && parseFloat(getComputedStyle(el).paddingBottom) <= 6;
                }"""), (width, "excess navigation padding")
            assert page.locator("[data-ui~=app-header] [data-ui~=avatar]").evaluate("""el => {
                const frame = el.getBoundingClientRect();
                const image = el.querySelector('img').getBoundingClientRect();
                const style = getComputedStyle(el);
                const border = parseFloat(style.borderLeftWidth);
                return style.padding === '0px' && Math.abs(image.width - frame.width + 2*border) < 0.1
                    && Math.abs(image.height - frame.height + 2*border) < 0.1;
            }"""), (width, "avatar does not fill its circle")
            assert page.evaluate("""() => document.querySelector('[data-ui~=adventure-copy] [data-ui~=primary]')
                .getBoundingClientRect().bottom <= document.querySelector('[data-ui~=bottom-nav]')
                .getBoundingClientRect().top"""), (
                width,
                "home action under navigation",
            )
            page.get_by_role("button", name="Мои поездки", exact=True).click()
            settled("trips-empty")
            assert page.evaluate(
                "document.documentElement.scrollHeight <= innerHeight"
            ), (width, "empty trips scroll")
            # Extra content must still scroll naturally; never hide overflow to mask it.
            page.locator("[data-ui~=trips-page]").evaluate("""el => {
                const extra = document.createElement('div'); extra.style.height = '1800px';
                extra.id = 'overflow-check'; el.append(extra);
            }""")
            assert page.evaluate("document.documentElement.scrollHeight > innerHeight")
            page.locator("#overflow-check").evaluate("el => el.remove()")
            page.get_by_role("button", name="О сервисе", exact=True).click()
            settled("profile")
            expect(page.locator("[data-ui~=about-profile]")).to_contain_text("Анна")
            expect(page.locator("#session-label")).to_have_text(
                "Все ваши поездки привязаны к профилю в MAX"
            )
            expect(
                page.get_by_text("Иллюстрации созданы с ИИ", exact=False)
            ).to_have_count(0)
            page.get_by_role("button", name="Главная", exact=True).click()
            page.get_by_role("button", name="Спланировать поездку").click()
            for step in range(5):
                expect(
                    page.get_by_label(f"Шаг {step + 1} из 5", exact=True)
                ).to_be_visible()
                settled(f"step-{step + 1}")
                assert page.locator("[data-ui~=wizard-actions] > [data-ui~=primary]").evaluate("""el => {
                    const r = el.getBoundingClientRect();
                    return r.top >= 0 && r.bottom <= innerHeight &&
                        el.contains(document.elementFromPoint(r.x+r.width/2, r.y+r.height/2));
                }"""), (width, step, "wizard action not reachable")
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                assert page.evaluate("""() => document.querySelector('[data-ui~=step-content]')
                    .getBoundingClientRect().bottom <= document.querySelector('[data-ui~=wizard-actions]')
                    .getBoundingClientRect().top + 1"""), (
                    width,
                    step,
                    "last field covered",
                )
                if step < 4:
                    page.locator("#next-step").click()
            assert not errors, errors
            print(f"Compact UI passed: {width} × {height}", flush=True)
            context.close()
        browser.close()


if __name__ == "__main__":
    main()
