import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from webgemini_cli.auth_manager import load_cookies, login
from webgemini_cli.gemini_client import GeminiClient

console = Console()


@click.group()
def cli() -> None:
    pass


@cli.command()
async def auth() -> None:
    console.print("[bold blue]Starting authentication...[/bold blue]")
    try:
        cookies = await login()
        console.print(
            f"[bold green]Authentication successful![/bold green] Captured {len(cookies)} cookies."
        )
    except Exception as e:
        console.print(f"[bold red]Authentication failed:[/bold red] {e}")
        sys.exit(1)


@cli.command()
def list() -> None:
    cookies = load_cookies()
    if not cookies:
        console.print("[bold red]Not authenticated. Run 'webgemini auth' first.[/bold red]")
        sys.exit(1)

    client = GeminiClient(cookies)
    chats = client.list_chats()

    if not chats:
        console.print("[yellow]No chats found.[/yellow]")
        return

    table = Table(title="Gemini Chats")
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="green")

    for chat in chats:
        table.add_row(chat["id"], chat["title"])

    console.print(table)


@cli.command()
@click.argument("conversation_id")
def fetch(conversation_id: str) -> None:
    cookies = load_cookies()
    if not cookies:
        console.print("[bold red]Not authenticated. Run 'webgemini auth' first.[/bold red]")
        sys.exit(1)

    client = GeminiClient(cookies)
    messages = client.fetch_chat(conversation_id)

    if not messages:
        console.print(f"[yellow]No messages found for conversation {conversation_id}.[/yellow]")
        return

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        console.print(f"[bold {('green' if role == 'user' else 'blue')}]--- {role.upper()} ---[/]")
        console.print(content)
        console.print()


@cli.command()
@click.argument("conversation_id")
@click.argument("message")
def continue_chat(conversation_id: str, message: str) -> None:
    cookies = load_cookies()
    if not cookies:
        console.print("[bold red]Not authenticated. Run 'webgemini auth' first.[/bold red]")
        sys.exit(1)

    client = GeminiClient(cookies)
    response = client.continue_chat(conversation_id, message)
    console.print(f"[bold green]Response:[/bold green] {response}")


@cli.command()
@click.argument("conversation_id")
@click.argument("output_file", type=click.Path())
def export(conversation_id: str, output_file: Path) -> None:
    cookies = load_cookies()
    if not cookies:
        console.print("[bold red]Not authenticated. Run 'webgemini auth' first.[/bold red]")
        sys.exit(1)

    client = GeminiClient(cookies)
    messages = client.fetch_chat(conversation_id)

    if not messages:
        console.print(f"[yellow]No messages found for conversation {conversation_id}.[/yellow]")
        return

    md_content = f"# Conversation: {conversation_id}\n\n"
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        md_content += f"## {role.upper()}\n\n{content}\n\n---\n\n"

    output_file.write_text(md_content)
    console.print(f"[bold green]Exported to {output_file}[/bold green]")
