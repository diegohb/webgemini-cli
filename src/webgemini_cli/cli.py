import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from webgemini_cli.auth_manager import load_cookies, login
from webgemini_cli.exceptions import (
    AuthenticationError,
    CookieExpiredError,
    ConversationNotFoundError,
    GeminiAPIError,
)
from webgemini_cli.gemini_client import GeminiClient
from webgemini_cli.logging_config import setup_logging

console = Console()


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose logging")
def cli(verbose: bool) -> None:
    if verbose:
        setup_logging(verbose=True)


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
@click.option(
    "-n", "--limit", default=10, help="Maximum number of chats to display (default: 10, max: 50)"
)
def list(limit: int) -> None:
    if limit < 1:
        limit = 1
    elif limit > 50:
        limit = 50

    try:
        cookies = load_cookies()
    except CookieExpiredError as e:
        console.print(f"[bold red]Session expired:[/bold red] {e}")
        console.print("[bold yellow]Run 'webgemini auth' to re-authenticate.[/bold yellow]")
        sys.exit(2)
    except AuthenticationError as e:
        console.print(f"[bold red]Not authenticated:[/bold red] {e}")
        console.print("[bold yellow]Run 'webgemini auth' to authenticate.[/bold yellow]")
        sys.exit(2)

    try:
        client = GeminiClient(cookies)
        chats = client.list_chats()
    except CookieExpiredError as e:
        console.print(f"[bold red]Session expired:[/bold red] {e}")
        console.print("[bold yellow]Run 'webgemini auth' to re-authenticate.[/bold yellow]")
        sys.exit(2)
    except AuthenticationError as e:
        console.print(f"[bold red]Authentication error:[/bold red] {e}")
        console.print("[bold yellow]Run 'webgemini auth' to re-authenticate.[/bold yellow]")
        sys.exit(2)
    except GeminiAPIError as e:
        console.print(f"[bold red]API error:[/bold red] {e}")
        sys.exit(1)

    if not chats:
        console.print("[yellow]No chats found.[/yellow]")
        return

    table = Table(title="Gemini Chats")
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="green")

    for chat in chats[:limit]:
        table.add_row(chat["id"], chat["title"])

    console.print(table)


@cli.command()
@click.argument("conversation_id")
@click.option(
    "--format", "-f", "output_format", default="text", type=click.Choice(["text", "json"])
)
def fetch(conversation_id: str, output_format: str) -> None:
    if not conversation_id or not conversation_id.strip():
        console.print("[bold red]Error:[/bold red] conversation_id cannot be empty.")
        sys.exit(1)

    try:
        cookies = load_cookies()
    except CookieExpiredError as e:
        console.print(f"[bold red]Session expired:[/bold red] {e}")
        console.print("[bold yellow]Run 'webgemini auth' to re-authenticate.[/bold yellow]")
        sys.exit(2)
    except AuthenticationError as e:
        console.print(f"[bold red]Not authenticated:[/bold red] {e}")
        console.print("[bold yellow]Run 'webgemini auth' to authenticate.[/bold yellow]")
        sys.exit(2)

    try:
        client = GeminiClient(cookies)
        messages = client.fetch_chat(conversation_id)
    except ConversationNotFoundError as e:
        console.print(f"[bold red]Conversation not found:[/bold red] {e}")
        console.print(
            "[bold yellow]Run 'webgemini list' to see available conversations.[/bold yellow]"
        )
        sys.exit(1)
    except CookieExpiredError as e:
        console.print(f"[bold red]Session expired:[/bold red] {e}")
        console.print("[bold yellow]Run 'webgemini auth' to re-authenticate.[/bold yellow]")
        sys.exit(2)
    except AuthenticationError as e:
        console.print(f"[bold red]Authentication error:[/bold red] {e}")
        console.print("[bold yellow]Run 'webgemini auth' to re-authenticate.[/bold yellow]")
        sys.exit(2)
    except GeminiAPIError as e:
        console.print(f"[bold red]API error:[/bold red] {e}")
        sys.exit(1)

    if not messages:
        console.print(f"[yellow]No messages found for conversation {conversation_id}.[/yellow]")
        return

    if output_format == "json":
        import json

        console.print(json.dumps(messages, indent=2))
    else:
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            console.print(
                f"[bold {('green' if role == 'user' else 'blue')}]--- {role.upper()} ---[/]"
            )
            console.print(content)
            console.print()


@cli.command()
@click.argument("conversation_id")
@click.argument("message")
def continue_chat(conversation_id: str, message: str) -> None:
    if not conversation_id or not conversation_id.strip():
        console.print("[bold red]Error:[/bold red] conversation_id cannot be empty.")
        sys.exit(1)
    if not message or not message.strip():
        console.print("[bold red]Error:[/bold red] message cannot be empty.")
        sys.exit(1)

    try:
        cookies = load_cookies()
    except CookieExpiredError as e:
        console.print(f"[bold red]Session expired:[/bold red] {e}")
        console.print("[bold yellow]Run 'webgemini auth' to re-authenticate.[/bold yellow]")
        sys.exit(2)
    except AuthenticationError as e:
        console.print(f"[bold red]Not authenticated:[/bold red] {e}")
        console.print("[bold yellow]Run 'webgemini auth' to authenticate.[/bold yellow]")
        sys.exit(2)

    try:
        client = GeminiClient(cookies)
        response = client.continue_chat(conversation_id, message)
        console.print(f"[bold green]Response:[/bold green] {response}")
    except ConversationNotFoundError as e:
        console.print(f"[bold red]Conversation not found:[/bold red] {e}")
        console.print(
            "[bold yellow]Run 'webgemini list' to see available conversations.[/bold yellow]"
        )
        sys.exit(1)
    except CookieExpiredError as e:
        console.print(f"[bold red]Session expired:[/bold red] {e}")
        console.print("[bold yellow]Run 'webgemini auth' to re-authenticate.[/bold yellow]")
        sys.exit(2)
    except AuthenticationError as e:
        console.print(f"[bold red]Authentication error:[/bold red] {e}")
        console.print("[bold yellow]Run 'webgemini auth' to re-authenticate.[/bold yellow]")
        sys.exit(2)
    except GeminiAPIError as e:
        console.print(f"[bold red]API error:[/bold red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("conversation_id")
@click.argument("output_file", type=click.Path())
@click.option("-o", "--output", "output_path", type=click.Path(), help="Custom output path")
def export(conversation_id: str, output_file: Path, output_path: Path | None) -> None:
    if not conversation_id or not conversation_id.strip():
        console.print("[bold red]Error:[/bold red] conversation_id cannot be empty.")
        sys.exit(1)

    final_output_path = output_path or output_file

    try:
        cookies = load_cookies()
    except CookieExpiredError as e:
        console.print(f"[bold red]Session expired:[/bold red] {e}")
        console.print("[bold yellow]Run 'webgemini auth' to re-authenticate.[/bold yellow]")
        sys.exit(2)
    except AuthenticationError as e:
        console.print(f"[bold red]Not authenticated:[/bold red] {e}")
        console.print("[bold yellow]Run 'webgemini auth' to authenticate.[/bold yellow]")
        sys.exit(2)

    try:
        client = GeminiClient(cookies)
        messages = client.fetch_chat(conversation_id)
    except ConversationNotFoundError as e:
        console.print(f"[bold red]Conversation not found:[/bold red] {e}")
        console.print(
            "[bold yellow]Run 'webgemini list' to see available conversations.[/bold yellow]"
        )
        sys.exit(1)
    except CookieExpiredError as e:
        console.print(f"[bold red]Session expired:[/bold red] {e}")
        console.print("[bold yellow]Run 'webgemini auth' to re-authenticate.[/bold yellow]")
        sys.exit(2)
    except AuthenticationError as e:
        console.print(f"[bold red]Authentication error:[/bold red] {e}")
        console.print("[bold yellow]Run 'webgemini auth' to re-authenticate.[/bold yellow]")
        sys.exit(2)
    except GeminiAPIError as e:
        console.print(f"[bold red]API error:[/bold red] {e}")
        sys.exit(1)

    if not messages:
        console.print(f"[yellow]No messages found for conversation {conversation_id}.[/yellow]")
        return

    md_content = f"# Conversation: {conversation_id}\n\n"
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        md_content += f"## {role.upper()}\n\n{content}\n\n---\n\n"

    final_output_path.write_text(md_content)
    console.print(f"[bold green]Exported to {final_output_path}[/bold green]")


@cli.command()
def status() -> None:
    from webgemini_cli.config import _get_config_dir, get_storage_state_path

    storage_path = get_storage_state_path()
    config_dir = _get_config_dir()

    console.print("[bold]webgemini-cli Status[/bold]")
    console.print()
    console.print(f"Config directory: [cyan]{config_dir}[/cyan]")
    console.print(f"Storage file: [cyan]{storage_path}[/cyan]")
    console.print()

    if not storage_path.exists():
        console.print("[bold red]Status: Not authenticated[/bold red]")
        console.print("[yellow]Run 'webgemini auth' to authenticate.[/yellow]")
        sys.exit(2)

    try:
        cookies = load_cookies()
        client = GeminiClient(cookies)
        client.list_chats()
        console.print("[bold green]Status: Authenticated and connected[/bold green]")
        console.print("[green]Cookies are valid and API connection is working.[/green]")
    except CookieExpiredError:
        console.print("[bold yellow]Status: Session expired[/bold yellow]")
        console.print("[yellow]Run 'webgemini auth' to re-authenticate.[/yellow]")
        sys.exit(2)
    except AuthenticationError:
        console.print("[bold red]Status: Authentication invalid[/bold red]")
        console.print("[yellow]Run 'webgemini auth' to re-authenticate.[/yellow]")
        sys.exit(2)
    except GeminiAPIError as e:
        console.print("[bold yellow]Status: API connection issue[/bold yellow]")
        console.print(f"[yellow]Error: {e}[/yellow]")
        console.print(
            "[yellow]The cookies may be valid but the API is not responding properly.[/yellow]"
        )
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Status: Unknown error[/bold red]")
        console.print(f"[red]{e}[/red]")
        sys.exit(1)
