import time
from functools import wraps
from typing import Any, Callable, TypeVar

import requests

from gemini import Gemini
from gemini.src.misc.constants import URLs

from webgemini_cli.exceptions import (
    AuthenticationError,
    CookieExpiredError,
    ConversationNotFoundError,
    GeminiAPIError,
)
from webgemini_cli.logging_config import get_logger

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

MAX_RETRIES = 2
INITIAL_BACKOFF = 1


def retry_on_auth_failure(func: F) -> F:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        last_exception: Exception | None = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                return func(*args, **kwargs)
            except (AuthenticationError, CookieExpiredError) as e:
                logger.debug(f"Auth error on attempt {attempt + 1}: {e}")
                if attempt < MAX_RETRIES:
                    logger.debug("Retrying after auth error...")
                last_exception = e
            except requests.RequestException as e:
                logger.debug(f"Network error on attempt {attempt + 1}: {e}")
                if attempt < MAX_RETRIES:
                    backoff = INITIAL_BACKOFF * (2**attempt)
                    logger.debug(f"Retrying after {backoff}s backoff...")
                    time.sleep(backoff)
                else:
                    last_exception = GeminiAPIError(
                        f"Network error after {MAX_RETRIES} retries: {e}"
                    )
        if last_exception is not None:
            raise last_exception
        raise GeminiAPIError("Unexpected error in retry logic")

    return wrapper  # type: ignore[return-value]


class GeminiClient:
    def __init__(self, cookies: dict[str, str]) -> None:
        self._cookies = cookies
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.9",
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        for key, value in cookies.items():
            self._session.cookies.set(key, value)
        self._gemini = Gemini(cookies=cookies)
        self._setup_session()

    def _setup_session(self) -> None:
        try:
            response = self._session.get(URLs.BASE_URL.value, cookies=self._cookies, timeout=30)
            if response.status_code == 401 or response.status_code == 403:
                raise AuthenticationError("Authentication failed. Please re-authenticate.")
            logger.debug(f"Session setup response status: {response.status_code}")
        except requests.RequestException as e:
            logger.debug(f"Session setup request failed: {e}")

    def _extract_text(self, response: Any) -> str:
        if hasattr(response, "text"):
            return response.text
        return str(response)

    @retry_on_auth_failure
    def list_chats(self) -> list[dict[str, str]]:
        url = (
            f"{URLs.BASE_URL.value}/_/BardChatUi/data/assistant.lamda.BardFrontendService/GetChats"
        )
        params = {
            "hl": "en",
            "_reqid": "0",
            "rt": "b",
        }
        try:
            response = self._session.get(url, params=params, cookies=self._cookies, timeout=30)
            if response.status_code == 401 or response.status_code == 403:
                raise AuthenticationError("Authentication failed. Please re-authenticate.")
            if response.status_code == 200:
                data = response.json()
                return self._parse_chat_list(data)
            raise GeminiAPIError(f"Unexpected response status: {response.status_code}")
        except requests.RequestException as e:
            logger.debug(f"list_chats request failed: {e}")
            raise

    def _parse_chat_list(self, data: Any) -> list[dict[str, str]]:
        chats = []
        try:
            if isinstance(data, list) and len(data) > 0:
                for item in data[0]:
                    if isinstance(item, dict):
                        chat_id = item.get("id", "")
                        title = item.get("title", "Untitled")
                        chats.append({"id": chat_id, "title": title})
        except (IndexError, KeyError, TypeError):
            logger.debug("Failed to parse chat list data")
        return chats

    @retry_on_auth_failure
    def fetch_chat(self, conversation_id: str) -> list[dict[str, str]]:
        url = f"{URLs.BASE_URL.value}/_/BardChatUi/data/assistant.lamda.BardFrontendService/GetChat"
        params = {
            "hl": "en",
            "_reqid": "0",
            "rt": "b",
        }
        data = {
            "conversationId": conversation_id,
        }
        try:
            response = self._session.post(
                url, params=params, json=data, cookies=self._cookies, timeout=30
            )
            if response.status_code == 401 or response.status_code == 403:
                raise AuthenticationError("Authentication failed. Please re-authenticate.")
            if response.status_code == 404:
                raise ConversationNotFoundError(
                    f"Conversation '{conversation_id}' not found. "
                    "Run 'webgemini list' to see available conversations."
                )
            if response.status_code == 200:
                return self._parse_chat_history(response.json(), conversation_id)
            raise GeminiAPIError(f"Unexpected response status: {response.status_code}")
        except requests.RequestException as e:
            logger.debug(f"fetch_chat request failed: {e}")
            raise

    def _parse_chat_history(self, data: Any, conversation_id: str) -> list[dict[str, str]]:
        messages = []
        try:
            if isinstance(data, list) and len(data) > 1:
                conversation = data[1]
                if isinstance(conversation, list):
                    for msg in conversation:
                        if isinstance(msg, dict):
                            role = msg.get("role", "user")
                            content = msg.get("content", "")
                            messages.append(
                                {
                                    "role": role,
                                    "content": content,
                                    "conversation_id": conversation_id,
                                }
                            )
        except (IndexError, KeyError, TypeError):
            logger.debug("Failed to parse chat history data")
        return messages

    @retry_on_auth_failure
    def continue_chat(self, conversation_id: str, message: str) -> str:
        self._gemini.rcid = conversation_id
        try:
            response = self._gemini.generate_content(message)
            return self._extract_text(response)
        except Exception as e:
            logger.debug(f"continue_chat failed: {e}")
            raise
