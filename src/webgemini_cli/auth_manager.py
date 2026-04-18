import json
from datetime import datetime, timedelta

from playwright.async_api import async_playwright

from webgemini_cli.config import ensure_config_dir, get_storage_state_path
from webgemini_cli.exceptions import AuthenticationError, CookieExpiredError

REQUIRED_COOKIES = {"__Secure-1PSID", "__Secure-1PSIDTS"}
COOKIE_EXPIRY_THRESHOLD_DAYS = 7


def validate_cookies(cookies: dict) -> bool:
    if not cookies or "cookies" not in cookies:
        return False
    cookie_list = cookies.get("cookies", [])
    cookie_names = {c.get("name") for c in cookie_list if isinstance(c, dict)}
    return REQUIRED_COOKIES.issubset(cookie_names)


def check_cookie_freshness(cookies: dict) -> bool:
    if not cookies or "cookies" not in cookies:
        return False
    cookie_list = cookies.get("cookies", [])
    for cookie in cookie_list:
        if isinstance(cookie, dict) and cookie.get("name") == "__Secure-1PSIDTS":
            expires = cookie.get("expires", -1)
            if expires > 0:
                expiry_date = datetime.fromtimestamp(expires)
                threshold = datetime.now() + timedelta(days=COOKIE_EXPIRY_THRESHOLD_DAYS)
                if expiry_date < threshold:
                    return False
    return True


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


def load_cookies() -> tuple[str, str | None]:
    storage_path = get_storage_state_path()
    if not storage_path.exists():
        raise AuthenticationError(
            f"Authentication required. Run 'webgemini auth' to authenticate. "
            f"Storage file not found at {storage_path}"
        )
    with open(storage_path) as f:
        cookies = json.load(f)
    if not check_cookie_freshness(cookies):
        raise CookieExpiredError(
            "Session appears to be expired. Please run 'webgemini auth' to re-authenticate."
        )
    cookie_dict = {c["name"]: c["value"] for c in cookies.get("cookies", [])}
    secure_1psid = cookie_dict.get("__Secure-1PSID")
    secure_1psidts = cookie_dict.get("__Secure-1PSIDTS")
    if not secure_1psid:
        raise AuthenticationError("Missing required cookie __Secure-1PSID")
    return (secure_1psid, secure_1psidts)


async def refresh_cookies() -> tuple[str, str | None]:
    cookies = await login()
    cookie_dict = {c["name"]: c["value"] for c in cookies}
    secure_1psid = cookie_dict.get("__Secure-1PSID")
    secure_1psidts = cookie_dict.get("__Secure-1PSIDTS")
    if not secure_1psid:
        raise AuthenticationError("Missing required cookie __Secure-1PSID")
    return (secure_1psid, secure_1psidts)
