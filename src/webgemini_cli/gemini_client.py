from typing import Any

import requests

from gemini import Gemini
from gemini.src.misc.constants import URLs


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
            self._session.get(URLs.BASE_URL.value, cookies=self._cookies, timeout=30)
        except requests.RequestException:
            pass

    def _extract_text(self, response: Any) -> str:
        if hasattr(response, "text"):
            return response.text
        return str(response)

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
            if response.status_code == 200:
                data = response.json()
                return self._parse_chat_list(data)
        except requests.RequestException:
            pass
        return []

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
            pass
        return chats

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
            if response.status_code == 200:
                return self._parse_chat_history(response.json(), conversation_id)
        except requests.RequestException:
            pass
        return []

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
            pass
        return messages

    def continue_chat(self, conversation_id: str, message: str) -> str:
        self._gemini.rcid = conversation_id
        response = self._gemini.generate_content(message)
        return self._extract_text(response)
