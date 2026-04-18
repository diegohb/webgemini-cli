import asyncio

from gemiterm.auth_manager import load_cookies
from gemiterm.gemini_client import GeminiClient


async def main() -> None:
    cookies = load_cookies()
    if not cookies:
        print("Not authenticated. Run 'gemiterm auth' first.")
        return

    client = GeminiClient(cookies)

    print("Fetching list of chats...")
    chats = client.list_chats()
    if not chats:
        print("No chats found.")
        return

    print(f"Found {len(chats)} chats. Showing 5 most recent:")
    for i, chat in enumerate(chats[:5]):
        print(f"  {i + 1}. {chat['title']} (ID: {chat['id']})")

    if chats:
        most_recent = chats[0]
        print(f"\nAppending 'Hello from the API' to the most recent chat: {most_recent['title']}")
        response = client.continue_chat(most_recent["id"], "Hello from the API")
        print(f"Response: {response}")
        print("\nActions completed successfully.")


if __name__ == "__main__":
    asyncio.run(main())
