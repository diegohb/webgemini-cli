import asyncio
from typing import Any

from gemini_webapi import ChatHistory, ChatSession, GeminiClient as WebAPIClient

from gemiterm.exceptions import GeminiAPIError
from gemiterm.logging_config import get_logger

logger = get_logger(__name__)


class GeminiClient:
    def __init__(self, secure_1psid: str, secure_1psidts: str | None = None) -> None:
        self._secure_1psid = secure_1psid
        self._secure_1psidts = secure_1psidts
        self._client: WebAPIClient | None = None
        self._chat_sessions: dict[str, ChatSession] = {}
        self._loop: asyncio.AbstractEventLoop | None = None

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        return self._loop

    def _ensure_client(self) -> WebAPIClient:
        if self._client is None:
            self._client = WebAPIClient(self._secure_1psid, self._secure_1psidts)
            loop = self._get_loop()
            loop.run_until_complete(self._client.init())
        return self._client

    def list_chats(self) -> list[dict[str, Any]]:
        try:
            client = self._ensure_client()
            chats = client.list_chats()
            if chats is None:
                return []
            return [
                {
                    "id": chat.cid,
                    "title": chat.title,
                    "is_pinned": getattr(chat, "is_pinned", False),
                    "timestamp": getattr(chat, "timestamp", 0),
                }
                for chat in chats
            ]
        except Exception as e:
            logger.debug(f"list_chats failed: {e}")
            raise GeminiAPIError(f"Failed to list chats: {e}")

    def fetch_chat(self, conversation_id: str) -> list[dict[str, Any]]:
        try:
            client = self._ensure_client()
            loop = self._get_loop()
            history = loop.run_until_complete(client.read_chat(conversation_id))
            if history is None:
                return []
            return self._parse_chat_history(history, conversation_id)
        except Exception as e:
            logger.debug(f"fetch_chat failed: {e}")
            raise GeminiAPIError(f"Failed to fetch chat: {e}")

    def _parse_chat_history(
        self, history: ChatHistory, conversation_id: str
    ) -> list[dict[str, Any]]:
        messages = []
        for turn in history.turns:
            messages.append(
                {
                    "role": turn.role,
                    "content": turn.text,
                    "conversation_id": conversation_id,
                }
            )
        return messages

    def continue_chat(self, conversation_id: str, message: str) -> str:
        try:
            client = self._ensure_client()
            loop = self._get_loop()
            if conversation_id in self._chat_sessions:
                chat = self._chat_sessions[conversation_id]
            else:
                metadata = {"cid": conversation_id}
                chat = client.start_chat(metadata=metadata)
                self._chat_sessions[conversation_id] = chat
            response = loop.run_until_complete(chat.send_message(message))
            return response.text
        except Exception as e:
            logger.debug(f"continue_chat failed: {e}")
            raise GeminiAPIError(f"Failed to continue chat: {e}")
