import json
import sys
from typing import Any

from webgemini_cli.gemini_client import GeminiClient
from webgemini_cli.exceptions import (
    AuthenticationError,
    CookieExpiredError,
    ConversationNotFoundError,
    GeminiAPIError,
    WebGeminiError,
)


def handle_list_chats(cookies: dict[str, str], params: dict[str, Any]) -> list[dict[str, str]]:
    client = GeminiClient(cookies)
    return client.list_chats()


def handle_fetch_chat(cookies: dict[str, str], params: dict[str, Any]) -> list[dict[str, str]]:
    conversation_id = params.get("conversation_id", "")
    client = GeminiClient(cookies)
    return client.fetch_chat(conversation_id)


def handle_continue_chat(cookies: dict[str, str], params: dict[str, Any]) -> str:
    conversation_id = params.get("conversation_id", "")
    message = params.get("message", "")
    client = GeminiClient(cookies)
    return client.continue_chat(conversation_id, message)


HANDLERS = {
    "list_chats": handle_list_chats,
    "fetch_chat": handle_fetch_chat,
    "continue_chat": handle_continue_chat,
}


def process_request(request: dict[str, Any]) -> dict[str, Any]:
    command = request.get("command")
    cookies = request.get("cookies", {})
    params = request.get("params", {})

    if command not in HANDLERS:
        return {
            "success": False,
            "data": None,
            "error": {"type": "ValueError", "message": f"Unknown command: {command}"},
        }

    handler = HANDLERS[command]
    try:
        result = handler(cookies, params)
        return {"success": True, "data": result, "error": None}
    except WebGeminiError as e:
        error_type = type(e).__name__
        return {"success": False, "data": None, "error": {"type": error_type, "message": str(e)}}
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": {"type": "Exception", "message": str(e)},
        }


def main() -> None:
    try:
        request = json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        response = {
            "success": False,
            "data": None,
            "error": {"type": "JSONDecodeError", "message": f"Invalid JSON input: {e}"},
        }
        print(json.dumps(response))
        return

    response = process_request(request)
    print(json.dumps(response))


if __name__ == "__main__":
    main()
