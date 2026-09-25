"""Browser checks for curated routes. No live generation or messages."""

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
    cities = [
        ("Коломна", "Москва", 1),
        ("Суздаль", "Москва", 2),
        ("Выборг", "Санкт-Петербург", 1),
        ("Великий Новгород", "Санкт-Петербург", 1),
    ]
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        for width, height in [(320, 633), (390, 844), (450, 633), (1360, 633)]:
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
                    json={"mode": "max", "user": {"id": 42, "first_name": "Анна"}}
                ),
            )
            submissions = []

            def block_generation(route, submissions=submissions):
                submissions.append(route.request.method)
                route.fulfill(
                    status=503,
                    json={"error": "Unexpected generation in preset preview"},
                )

            context.route("**/api/v1/trips/jobs", block_generation)
            context.route("**/api/v1/trips", lambda r: r.fulfill(json={"items": [], "total": 0, "next_cursor": None}))
            context.route("**/api/v1/cities/validate?*", lambda r: r.fulfill(json={"city": {"title": "Коломна"}, "distance_km": 100}))
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda error, errors=errors: errors.append(str(error)))
            page.goto(args.base_url, wait_until="networkidle")
            page.get_by_role("button", name="Пропустить знакомство").click()
            expect(page.locator("[data-ui~=preset-card]")).to_have_count(2)
            assert (
                page.locator("[data-ui~=how-card] h3").evaluate(
                    "el => parseFloat(getComputedStyle(el).fontSize)"
                )
                >= 13
            )
            for photo in page.locator("[data-ui~=preset-card] img").all():
                photo.scroll_into_view_if_needed()
                expect(photo).to_be_visible()
                photo.evaluate("el => el.decode()")
                assert photo.evaluate(
                    "el => el.naturalWidth >= 1000 && new URL(el.src).origin === location.origin"
                )
            assert (
                len(
                    set(
                        page.locator("[data-ui~=preset-card] img").evaluate_all(
                            "els => els.map(el => el.src)"
                        )
                    )
                )
                == 2
            )
            page.locator("[data-ui~=preset-section]").scroll_into_view_if_needed()
            if width in (390, 1360):
                page.screenshot(
                    path=str(screenshots / f"presets-{width}-cards.png"), full_page=True
                )
            page.evaluate("window.cityDocumentMarker = true")
            moscow_banner = page.locator("[data-ui~=adventure-card] > img").get_attribute("src")
            for index, (city, origin, days) in enumerate(cities):
                if (
                    page.get_by_label("Город отправления", exact=True).input_value()
                    != origin
                ):
                    page.get_by_label("Город отправления", exact=True).select_option(
                        origin
                    )
                    expect(page.locator("[data-ui~=origin-pill] > span")).to_have_text(origin)
                    assert page.evaluate("window.cityDocumentMarker === true")
                    assert (
                        page.locator("[data-ui~=adventure-card] > img").get_attribute("src")
                        != moscow_banner
                    )
                    expect(page.locator("[data-ui~=preset-card]")).to_have_count(2)
                    expect(
                        page.get_by_role(
                            "button", name="Открыть маршрут: Коломна", exact=True
                        )
                    ).to_have_count(0)
                    for photo in page.locator("[data-ui~=preset-card] img").all():
                        photo.scroll_into_view_if_needed()
                        photo.evaluate("el => el.decode()")
                        assert photo.evaluate("el => el.naturalWidth >= 1000")
                    if width in (390, 1360):
                        page.screenshot(
                            path=str(screenshots / f"presets-spb-{width}.png"),
                            full_page=True,
                        )

                page.get_by_role(
                    "button", name=f"Открыть маршрут: {city}", exact=True
                ).click()
                expect(page.locator("#preset-title")).to_contain_text(city)
                page.wait_for_timeout(200)
                assert page.evaluate(
                    "document.documentElement.scrollWidth <= innerWidth"
                ), (width, city)
                expect(page.locator("[data-ui~=preset-day]")).to_have_count(days)
                assert page.locator("[data-ui~=preset-timeline] li").count() >= days * 4
                assert page.locator("#use-preset").evaluate(
                    "el => el.getBoundingClientRect().bottom <= innerHeight"
                )
                expect(page.locator("[data-ui~=weather-card]")).to_have_count(0)
                page.locator("[data-ui~=preset-timeline] a").first.click()
                assert page.evaluate(
                    "window.WebApp.calls.some(x => typeof x === 'string' && x.startsWith('https://yandex.ru/maps/'))"
                )
                page.get_by_role("checkbox").first.check()
                expect(page.get_by_role("checkbox").first).to_be_checked()
                expect(
                    page.get_by_text("Источник фотографии", exact=True)
                ).to_have_count(0)
                expect(page.locator(".preset-photo-credit")).to_have_count(0)
                expect(page.locator("[data-ui~=venue-list] li").first).to_be_visible()
                venue = page.locator("[data-ui~=venue-list] a").first
                venue_url = venue.get_attribute("href")
                expect(venue).to_contain_text("Сайт")
                venue.click()
                assert page.evaluate(
                    "url => window.WebApp.calls.includes(url)", venue_url
                )
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                assert page.evaluate(
                    """() => document.querySelector('[data-ui~=preset-sources]').getBoundingClientRect().bottom <= document.querySelector('[data-ui~=preset-actions]').getBoundingClientRect().top + 1"""
                ), (width, city, "last content covered")
                if width == 390 and index in (0, 1):
                    page.screenshot(
                        path=str(screenshots / f"preset-{index}-mobile.png"),
                        full_page=True,
                    )
                page.locator("#use-preset").click()
                expect(page.locator("input[name=destination]")).to_have_value(city)
                expect(page.locator("select[name=origin]")).to_have_value(origin)
                page.locator("#next-step").click()
                expect(page.locator("input[name=start_date]")).to_be_visible()
                expect(page.locator("[data-ui~=duration-grid] [data-ui~=selected]")).to_contain_text(
                    str(days)
                )
                page.get_by_role("button", name="Закрыть анкету").click()
            page.get_by_label("Город отправления", exact=True).select_option("Москва")
            expect(page.locator("[data-ui~=origin-pill] > span")).to_have_text("Москва")
            expect(page.locator("[data-ui~=adventure-card] > img")).to_have_attribute(
                "src", moscow_banner
            )
            expect(
                page.get_by_role("button", name="Открыть маршрут: Коломна", exact=True)
            ).to_be_visible()
            expect(
                page.get_by_role("button", name="Открыть маршрут: Выборг", exact=True)
            ).to_have_count(0)
            assert page.evaluate("window.cityDocumentMarker === true")
            page.get_by_role("button", name="Спланировать поездку", exact=True).click()
            page.get_by_role("button", name="Предыдущий шаг", exact=True).click()
            expect(page.locator("input[name=destination]")).to_have_value(
                "Великий Новгород"
            )
            page.get_by_role("button", name="Закрыть анкету").click()
            page.get_by_role("button", name="О сервисе", exact=True).click()
            page.locator("[data-ui~=photo-credits] summary").click()
            expect(page.locator("[data-ui~=photo-credits] p")).to_have_count(4)
            expect(page.locator("[data-ui~=photo-credits]")).to_contain_text("Wikimedia Commons")
            page.get_by_role("button", name="Мои поездки", exact=True).click()
            expect(
                page.get_by_role("heading", name="Ваши открытия ещё впереди")
            ).to_be_visible()
            assert not submissions, submissions
            assert not errors, errors
            print(
                f"Presets passed: {width} × {height}; 4 photos, complete plans, links, packing and draft handoff.",
                flush=True,
            )
            context.close()
        browser.close()


if __name__ == "__main__":
    main()
