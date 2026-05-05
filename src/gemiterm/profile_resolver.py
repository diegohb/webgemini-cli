from typing import Any

from rich.console import Console

from gemiterm.auth_manager import list_profile_statuses, load_cookies
from gemiterm.error_handlers import require_active_profiles
from gemiterm.exceptions import (
    AuthenticationError,
    CookieExpiredError,
    ConversationNotFoundError,
    GeminiAPIError,
)
from gemiterm.gemini_client import GeminiClient

console = Console()


def get_default_client() -> tuple[GeminiClient, str, str | None]:
    """Load default profile cookies and return (client, secure_1psid, secure_1psidts)."""
    secure_1psid, secure_1psidts = load_cookies()
    client = GeminiClient(secure_1psid, secure_1psidts)
    return client, secure_1psid, secure_1psidts


def find_conversation_in_profiles(
    conversation_id: str,
) -> tuple[list[dict[str, Any]] | None, Exception | None]:
    """Search all active profiles for a conversation.

    Returns (messages, last_error). messages is None if not found.
    """
    statuses = list_profile_statuses()
    active_names = require_active_profiles(statuses)

    messages = None
    last_error = None
    for pname in active_names:
        try:
            secure_1psid, secure_1psidts = load_cookies(pname)
            client = GeminiClient(secure_1psid, secure_1psidts)
            messages = client.fetch_chat(conversation_id)
            break
        except ConversationNotFoundError:
            continue
        except (CookieExpiredError, AuthenticationError, GeminiAPIError) as e:
            last_error = e
            continue

    return messages, last_error


def find_client_for_conversation(
    conversation_id: str,
) -> tuple[str | None, str | None]:
    """Find which profile owns a conversation for continuing chat.

    Returns (secure_1psid, secure_1psidts) or (None, None) if not found.
    """
    statuses = list_profile_statuses()
    active_names = require_active_profiles(statuses)

    for pname in active_names:
        try:
            pname_1psid, pname_1psidts = load_cookies(pname)
            client = GeminiClient(pname_1psid, pname_1psidts)
            client.fetch_chat(conversation_id)
            secure_1psid, secure_1psidts = pname_1psid, pname_1psidts
            break
        except (ConversationNotFoundError, CookieExpiredError, AuthenticationError, GeminiAPIError):
            continue
    else:
        return None, None

    return secure_1psid, secure_1psidts


def collect_chats_from_all_profiles() -> list[dict[str, Any]]:
    """Collect and deduplicate chats from all active profiles."""
    statuses = list_profile_statuses()
    active_profiles = [s for s in statuses if s["is_active"]]
    if not active_profiles:
        return []

    all_chats: dict[str, dict[str, Any]] = {}
    for profile_status in active_profiles:
        pname = profile_status["name"]
        try:
            secure_1psid, secure_1psidts = load_cookies(pname)
            client = GeminiClient(secure_1psid, secure_1psidts)
            profile_chats = client.list_chats()
            for chat in profile_chats:
                chat["profile"] = pname
                all_chats[chat["id"]] = chat
        except Exception:
            continue

    return list(all_chats.values())
