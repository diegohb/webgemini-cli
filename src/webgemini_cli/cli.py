import json
import sys
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
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
@click.option("-o", "--output", "output_path", type=click.Path(), help="Custom output file path")
@click.option(
    "--format",
    "-f",
    "output_format",
    default="markdown",
    type=click.Choice(["markdown", "json"]),
    help="Export format (default: markdown)",
)
@click.option(
    "--include-metadata",
    is_flag=True,
    default=False,
    help="Include full metadata in export",
)
def export(
    conversation_id: str, output_path: Path | None, output_format: str, include_metadata: bool
) -> None:
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

    if output_path is None:
        date_str = datetime.now().strftime("%Y%m%d")
        extension = "md" if output_format == "markdown" else "json"
        default_filename = f"gemini-chat-{conversation_id}-{date_str}.{extension}"
        output_path = Path.cwd() / default_filename

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_format == "markdown":
        from webgemini_cli.exporter import format_chat_as_markdown

        title = f"Conversation: {conversation_id}"
        content = format_chat_as_markdown(
            messages, title, conversation_id=conversation_id, include_metadata=include_metadata
        )
    else:
        export_data = {
            "conversation_id": conversation_id,
            "message_count": len(messages),
            "messages": messages,
        }
        if include_metadata:
            export_data["metadata"] = {
                "title": f"Conversation: {conversation_id}",
                "export_date": datetime.now().isoformat(),
            }
        content = json.dumps(export_data, indent=2)

    output_path.write_text(content)
    console.print(f"[bold green]Exported to {output_path}[/bold green]")


@cli.command()
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    default=None,
    help="Directory to export conversations to (default: ./exports)",
)
@click.option(
    "--since",
    type=str,
    default=None,
    help="Export only conversations newer than this ISO date (e.g., 2024-01-01)",
)
@click.option(
    "--include-metadata",
    is_flag=True,
    default=False,
    help="Include full metadata in each export",
)
def export_all(output_dir: Path | None, since: str | None, include_metadata: bool) -> None:
    if output_dir is None:
        output_dir = Path.cwd() / "exports"

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

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
        all_chats = client.list_chats()
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

    if not all_chats:
        console.print("[yellow]No chats found.[/yellow]")
        return

    if since:
        try:
            datetime.fromisoformat(since)
        except ValueError:
            console.print(
                "[bold red]Error:[/bold red] Invalid date format for --since. Use ISO format (e.g., 2024-01-01)."
            )
            sys.exit(1)

    from webgemini_cli.exporter import format_chat_as_markdown

    exported_chats: list[dict[str, str]] = []
    failed_chats: list[tuple[str, str]] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        export_task = progress.add_task("[cyan]Exporting conversations...", total=len(all_chats))

        for chat in all_chats:
            conversation_id = chat["id"]
            title = chat["title"]

            progress.update(export_task, description=f"[cyan]Exporting: {title[:30]}...")

            try:
                messages = client.fetch_chat(conversation_id)
                if not messages:
                    progress.advance(export_task)
                    continue

                safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title)[:50]
                date_str = datetime.now().strftime("%Y%m%d")
                filename = f"gemini-chat-{conversation_id}-{safe_title[:20]}-{date_str}.md"
                filepath = output_path / filename

                content = format_chat_as_markdown(
                    messages,
                    title,
                    conversation_id=conversation_id,
                    include_metadata=include_metadata,
                )
                filepath.write_text(content)

                exported_chats.append(
                    {
                        "id": conversation_id,
                        "title": title,
                        "filename": filename,
                    }
                )
            except Exception as e:
                failed_chats.append((conversation_id, str(e)))

            progress.advance(export_task)

    if exported_chats:
        index_path = output_path / "_index.md"
        index_lines = ["# Exported Conversations\n"]
        index_lines.append(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        index_lines.append(f"Total: {len(exported_chats)} conversations\n")
        index_lines.append("---\n\n")

        for chat in sorted(exported_chats, key=lambda c: c["title"].lower()):
            index_lines.append(f"- [{chat['title']}]({chat['filename']}) (ID: {chat['id']})")

        index_path.write_text("\n".join(index_lines))
        console.print(f"[bold green]Created index: {index_path}[/bold green]")

    console.print(
        f"[bold green]Exported {len(exported_chats)} conversations to {output_path}[/bold green]"
    )

    if failed_chats:
        console.print(
            f"[bold yellow]Failed to export {len(failed_chats)} conversations:[/bold yellow]"
        )
        for cid, err in failed_chats:
            console.print(f"  - {cid}: {err}")


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
        console.print("[bold red]Status: Unknown error[/bold red]")
        console.print(f"[red]{e}[/red]")
        sys.exit(1)
