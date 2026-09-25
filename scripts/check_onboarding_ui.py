"""Profile-backed onboarding: delayed load/save, failure, fresh browser and manual replay."""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from playwright.async_api import async_playwright, expect

from scripts.check_ui import BRIDGE


async def check(base):
    profiles = set()
    writes = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome")
        for user_id, completed in [(42, False), (42, True), (43, False)]:
            context = await browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
            ready = asyncio.Event()
            save = asyncio.Event()
            fail = not completed
            errors = []
            await context.route("https://st.max.ru/**", lambda r: r.fulfill(
                content_type="application/javascript", body=BRIDGE))
            await context.route("**/api/v1/auth/me", lambda r: r.fulfill(
                json={"mode": "max", "user": {"id": user_id, "first_name": "Анна"}}))

            async def profile(route):
                await ready.wait()
                await route.fulfill(json={"onboarding_completed": user_id in profiles})

            async def complete(route):
                nonlocal fail
                assert route.request.method == "PUT"
                writes.append(user_id)
                await save.wait()
                if fail:
                    fail = False
                    await route.fulfill(status=503, json={"error": "Не удалось сохранить профиль"})
                else:
                    profiles.add(user_id)
                    await route.fulfill(json={"onboarding_completed": True})

            await context.route("**/api/v1/profile", profile)
            await context.route("**/api/v1/profile/onboarding", complete)
            page = await context.new_page()
            page.on("pageerror", lambda error: errors.append(str(error)))
            await page.goto(base, wait_until="domcontentloaded")
            onboarding = page.locator('[data-ui="onboarding"]')
            await expect(page.locator('[data-ui="boot-skeleton"]')).to_be_visible()
            await expect(onboarding).to_have_count(0)
            ready.set()
            if completed:
                await expect(page.get_by_role("button", name="О сервисе и вашем профиле", exact=True)).to_be_visible()
                await expect(onboarding).to_have_count(0)
                await page.get_by_role("button", name="О сервисе и вашем профиле", exact=True).click()
                await page.get_by_role("button", name="Посмотреть знакомство ещё раз").click()
                await expect(onboarding).to_be_visible()
                before = len(writes)
                await page.get_by_role("button", name="Пропустить знакомство").click()
                await expect(onboarding).to_have_count(0)
                assert len(writes) == before
                await page.reload(wait_until="networkidle")
                await expect(onboarding).to_have_count(0)
            else:
                await expect(onboarding).to_be_visible()
                if user_id == 42:
                    await page.get_by_role("button", name="Дальше", exact=True).click()
                    await page.get_by_role("button", name="Дальше", exact=True).click()
                    action = page.get_by_role("button", name="Начать путешествие")
                else:
                    action = page.get_by_role("button", name="Пропустить знакомство")
                await action.click()
                await expect(action).to_be_disabled()
                await page.keyboard.press("Escape")
                await expect(onboarding).to_be_visible()
                save.set()
                await expect(page.get_by_role("alert")).to_be_visible()
                assert writes.count(user_id) == 1
                await action.click()
                await expect(onboarding).to_have_count(0)
                assert writes.count(user_id) == 2
            assert not errors, errors
            await context.close()
        await browser.close()
    print("Onboarding passed: profile load, completion/skip, retry, duplicate guard, fresh browser, owner isolation, manual replay.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:18092")
    asyncio.run(check(parser.parse_args().base_url))
