import json

from playwright.async_api import async_playwright

from webgemini_cli.config import ensure_config_dir, get_storage_state_path


async def login() -> list[dict]:
    ensure_config_dir()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto("https://gemini.google.com")

        await page.wait_for_load_state("networkidle")

        while True:
            current_cookies = await context.cookies()
            cookie_names = {c["name"] for c in current_cookies}
            if "__Secure-1PSID" in cookie_names and "__Secure-1PSIDTS" in cookie_names:
                break
            await page.wait_for_timeout(500)

        cookies = await context.cookies()
        await context.storage_state(path=get_storage_state_path())
        await browser.close()

    return [dict(c) for c in cookies]


def load_cookies() -> dict:
    storage_path = get_storage_state_path()
    if not storage_path.exists():
        return {}
    with open(storage_path) as f:
        return json.load(f)
