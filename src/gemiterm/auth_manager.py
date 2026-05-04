import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from playwright.async_api import async_playwright

from gemiterm.config import (
    ensure_config_dir,
    get_profile_path,
    get_default_profile_name,
    list_profiles,
    set_default_profile_name,
)
from gemiterm.exceptions import AuthenticationError, CookieExpiredError

REQUIRED_COOKIES = {"__Secure-1PSID", "__Secure-1PSIDTS"}
COOKIE_EXPIRY_THRESHOLD_DAYS = 7


def _get_browser_executable() -> str | None:
    possible_paths = []

    local_browsers = Path.home() / "AppData" / "Local" / "ms-playwright"
    if local_browsers.exists():
        for rev in sorted(local_browsers.glob("chromium-*"), reverse=True):
            exe = rev / "chrome-win64" / "chrome.exe"
            if exe.exists():
                possible_paths.append(exe)

    if getattr(sys, "frozen", False):
        internal_browsers = (
            Path(sys._MEIPASS) / "playwright" / "driver" / "package" / ".local-browsers"
        )
        if internal_browsers.exists():
            for rev in sorted(internal_browsers.glob("chromium-*"), reverse=True):
                exe = rev / "chrome-win64" / "chrome.exe"
                if exe.exists():
                    possible_paths.append(exe)

    for path in possible_paths:
        if path.exists():
            return str(path)
    return None


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
                return expiry_date >= threshold
    return False


async def login(profile_name: str | None = None) -> list[dict]:
    if profile_name is None:
        profile_name = get_default_profile_name()
    ensure_config_dir()
    profile_path = get_profile_path(profile_name)
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        executable = _get_browser_executable()
        browser = await p.chromium.launch(headless=False, executable_path=executable)
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
        await context.storage_state(path=profile_path)
        await browser.close()

    if not list_profiles():
        set_default_profile_name(profile_name)
    return [dict(c) for c in cookies]


def load_cookies(profile_name: str | None = None) -> tuple[str, str | None]:
    if profile_name is None:
        profile_name = get_default_profile_name()
    storage_path = get_profile_path(profile_name)
    if not storage_path.exists():
        raise AuthenticationError(
            f"Authentication required. Run 'gemiterm auth' to authenticate. "
            f"Storage file not found at {storage_path}"
        )
    with open(storage_path) as f:
        cookies = json.load(f)
    if not check_cookie_freshness(cookies):
        raise CookieExpiredError(
            "Session appears to be expired. Please run 'gemiterm auth' to re-authenticate."
        )
    cookie_dict = {c["name"]: c["value"] for c in cookies.get("cookies", [])}
    secure_1psid = cookie_dict.get("__Secure-1PSID")
    secure_1psidts = cookie_dict.get("__Secure-1PSIDTS")
    if not secure_1psid:
        raise AuthenticationError("Missing required cookie __Secure-1PSID")
    return (secure_1psid, secure_1psidts)


async def refresh_cookies(profile_name: str | None = None) -> tuple[str, str | None]:
    cookies = await login(profile_name)
    cookie_dict = {c["name"]: c["value"] for c in cookies}
    secure_1psid = cookie_dict.get("__Secure-1PSID")
    secure_1psidts = cookie_dict.get("__Secure-1PSIDTS")
    if not secure_1psid:
        raise AuthenticationError("Missing required cookie __Secure-1PSID")
    return (secure_1psid, secure_1psidts)


def get_profile_status(profile_name: str) -> dict:
    profile_path = get_profile_path(profile_name)
    exists = profile_path.exists()
    if not exists:
        return {
            "exists": False,
            "is_active": False,
            "expires_at": None,
            "needs_refresh": True,
        }
    try:
        with open(profile_path) as f:
            cookies = json.load(f)
        is_active = check_cookie_freshness(cookies)
        expires_at = None
        needs_refresh = not is_active
        cookie_list = cookies.get("cookies", [])
        for cookie in cookie_list:
            if isinstance(cookie, dict) and cookie.get("name") == "__Secure-1PSIDTS":
                expires = cookie.get("expires", -1)
                if expires > 0:
                    dt = datetime.fromtimestamp(expires)
                    month = str(dt.month)
                    day = str(dt.day)
                    hour_12 = dt.strftime("%I")
                    hour = hour_12.lstrip("0")
                    expires_at = f"{month}/{day}/{dt.year} {hour}:{dt.strftime('%M%p')} ({dt.strftime('%A')})"
                    break
        return {
            "exists": True,
            "is_active": is_active,
            "expires_at": expires_at,
            "needs_refresh": needs_refresh,
        }
    except (json.JSONDecodeError, OSError):
        return {
            "exists": True,
            "is_active": False,
            "expires_at": None,
            "needs_refresh": True,
        }


def delete_profile(name: str) -> None:
    profile_dir = get_profile_path(name).parent
    if profile_dir.exists():
        import shutil
        shutil.rmtree(profile_dir)
    if get_default_profile_name() == name:
        remaining = list_profiles()
        if remaining:
            set_default_profile_name(remaining[0])


def rename_profile(old_name: str, new_name: str) -> None:
    old_dir = get_profile_path(old_name).parent
    new_dir = get_profile_path(new_name).parent
    if old_dir.exists():
        old_dir.rename(new_dir)
    if get_default_profile_name() == old_name:
        set_default_profile_name(new_name)


def list_profile_statuses() -> list[dict]:
    default_name = get_default_profile_name()
    profiles = list_profiles()
    statuses = []
    for name in profiles:
        status = get_profile_status(name)
        status["name"] = name
        status["is_default"] = name == default_name
        statuses.append(status)
    return statuses