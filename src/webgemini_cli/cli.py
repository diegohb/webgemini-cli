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
@click.option("-n", "--limit", default=10, help="Number of chats to display (default: 10)")
@click.option("-o", "--offset", default=0, help="Offset for pagination")
@click.option("--all", "fetch_all", is_flag=True, help="Fetch all cached chats")
@click.option(
    "--sort",
    type=click.Choice(["recent", "oldest", "alpha"]),
    default="recent",
    help="Sort order (default: recent)",
)
@click.option("-s", "--search", default=None, help="Search chat titles")
@click.option("--after", default=None, help="Show chats after ISO date (e.g., 2024-01-01)")
@click.option("--before", default=None, help="Show chats before ISO date (e.g., 2024-01-01)")
def list(
    limit: int,
    offset: int,
    fetch_all: bool,
    sort: str,
    search: str | None,
    after: str | None,
    before: str | None,
) -> None:
    if limit < 1:
        limit = 1

    try:
        secure_1psid, secure_1psidts = load_cookies()
    except CookieExpiredError as e:
        console.print(f"[bold red]Session expired:[/bold red] {e}")
        console.print("[bold yellow]Run 'webgemini auth' to re-authenticate.[/bold yellow]")
        sys.exit(2)
    except AuthenticationError as e:
        console.print(f"[bold red]Not authenticated:[/bold red] {e}")
        console.print("[bold yellow]Run 'webgemini auth' to authenticate.[/bold yellow]")
        sys.exit(2)

    try:
        client = GeminiClient(secure_1psid, secure_1psidts)
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

    effective_limit = 50 if fetch_all else limit
    effective_limit = min(effective_limit, 50)

    if sort == "recent":
        chats = sorted(chats, key=lambda c: (not c.get("is_pinned", False), -c.get("timestamp", 0)))
    elif sort == "oldest":
        chats = sorted(chats, key=lambda c: (not c.get("is_pinned", False), c.get("timestamp", 0)))
    elif sort == "alpha":
        chats = sorted(
            chats, key=lambda c: (not c.get("is_pinned", False), c.get("title", "").lower())
        )

    if search:
        chats = [c for c in chats if search.lower() in c.get("title", "").lower()]

    if after:
        try:
            after_ts = datetime.fromisoformat(after).timestamp()
            chats = [c for c in chats if c.get("timestamp", 0) >= after_ts]
        except ValueError:
            console.print(
                "[bold red]Error:[/bold red] Invalid date format for --after. Use ISO format (e.g., 2024-01-01)."
            )
            sys.exit(1)

    if before:
        try:
            before_ts = datetime.fromisoformat(before).timestamp()
            chats = [c for c in chats if c.get("timestamp", 0) <= before_ts]
        except ValueError:
            console.print(
                "[bold red]Error:[/bold red] Invalid date format for --before. Use ISO format (e.g., 2024-01-01)."
            )
            sys.exit(1)

    if offset >= len(chats):
        console.print("[yellow]No more chats to display.[/yellow]")
        return

    paginated_chats = chats[offset : offset + effective_limit]

    if not paginated_chats:
        console.print("[yellow]No chats found matching criteria.[/yellow]")
        return

    table = Table(title="Gemini Chats")
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="green")
    table.add_column("Pinned", style="yellow")
    table.add_column("Last Updated", style="blue")

    for chat in paginated_chats:
        pin_marker = "*" if chat.get("is_pinned") else ""
        ts = chat.get("timestamp")
        date_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M") if ts else "N/A"
        table.add_row(chat["id"], chat["title"], pin_marker, date_str)

    console.print(table)


@cli.command()
@click.argument("conversation_id")
@click.option(
    "--format", "-f", "output_format", default="text", type=click.Choice(["text", "json"])
)
@click.option(
    "--path",
    "-p",
    "output_path",
    type=click.Path(),
    default=None,
    help="File path to save fetched content (default: print to console)",
)
def fetch(conversation_id: str, output_format: str, output_path: Path | None) -> None:
    if not conversation_id or not conversation_id.strip():
        console.print("[bold red]Error:[/bold red] conversation_id cannot be empty.")
        sys.exit(1)

    try:
        secure_1psid, secure_1psidts = load_cookies()
    except CookieExpiredError as e:
        console.print(f"[bold red]Session expired:[/bold red] {e}")
        console.print("[bold yellow]Run 'webgemini auth' to re-authenticate.[/bold yellow]")
        sys.exit(2)
    except AuthenticationError as e:
        console.print(f"[bold red]Not authenticated:[/bold red] {e}")
        console.print("[bold yellow]Run 'webgemini auth' to authenticate.[/bold yellow]")
        sys.exit(2)

    try:
        client = GeminiClient(secure_1psid, secure_1psidts)
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

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output_format == "json" or output_path.suffix == ".json":
            content = json.dumps(messages, indent=2)
        else:
            lines = []
            for msg in messages:
                role = msg.get("role", "user")
                content_text = msg.get("content", "")
                lines.append(f"--- {role.upper()} ---")
                lines.append(content_text)
            content = "\n".join(lines)

        output_path.write_text(content)
        console.print(f"[bold green]Saved to {output_path}[/bold green]")
    else:
        if output_format == "json":
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


@cli.command(name="continue")
@click.argument("conversation_id")
@click.argument("message", required=False)
def continue_chat(conversation_id: str, message: str | None) -> None:
    if not conversation_id or not conversation_id.strip():
        console.print("[bold red]Error:[/bold red] conversation_id cannot be empty.")
        sys.exit(1)

    try:
        secure_1psid, secure_1psidts = load_cookies()
    except CookieExpiredError as e:
        console.print(f"[bold red]Session expired:[/bold red] {e}")
        console.print("[bold yellow]Run 'webgemini auth' to re-authenticate.[/bold yellow]")
        sys.exit(2)
    except AuthenticationError as e:
        console.print(f"[bold red]Not authenticated:[/bold red] {e}")
        console.print("[bold yellow]Run 'webgemini auth' to authenticate.[/bold yellow]")
        sys.exit(2)

    if message and message.strip():
        continue_chat_single(conversation_id, message, secure_1psid, secure_1psidts)
    else:
        continue_chat_interactive(conversation_id, secure_1psid, secure_1psidts)


def continue_chat_single(
    conversation_id: str, message: str, secure_1psid: str, secure_1psidts: str | None
) -> None:
    try:
        client = GeminiClient(secure_1psid, secure_1psidts)
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


def continue_chat_interactive(
    conversation_id: str, secure_1psid: str, secure_1psidts: str | None
) -> None:
    try:
        client = GeminiClient(secure_1psid, secure_1psidts)
    except Exception as e:
        console.print(f"[bold red]Failed to initialize client:[/bold red] {e}")
        sys.exit(1)

    console.print(f"[bold cyan]Interactive chat session started.[/bold cyan]")
    console.print("[dim]Type your message and press Enter to send.[/dim]")
    console.print("[dim]Type /exit or press Ctrl+C to end the session.[/dim]")
    console.print()

    while True:
        try:
            user_input = console.input("[bold green]>[/bold green] ")

            if user_input.strip().lower() == "/exit":
                console.print("[bold cyan]Ending chat session...[/bold cyan]")
                break

            if not user_input.strip():
                continue

            try:
                response = client.continue_chat(conversation_id, user_input)
                console.print(f"[bold blue]Response:[/bold blue] {response}")
                console.print()
            except ConversationNotFoundError as e:
                console.print(f"[bold red]Conversation not found:[/bold red] {e}")
                console.print(
                    "[bold yellow]Run 'webgemini list' to see available conversations.[/bold yellow]"
                )
                break
            except CookieExpiredError as e:
                console.print(f"[bold red]Session expired:[/bold red] {e}")
                console.print("[bold yellow]Run 'webgemini auth' to re-authenticate.[/bold yellow]")
                break
            except AuthenticationError as e:
                console.print(f"[bold red]Authentication error:[/bold red] {e}")
                console.print("[bold yellow]Run 'webgemini auth' to re-authenticate.[/bold yellow]")
                break
            except GeminiAPIError as e:
                console.print(f"[bold red]API error:[/bold red] {e}")
                console.print("[dim]Try sending another message or /exit to quit.[/dim]")
                console.print()

        except KeyboardInterrupt:
            console.print("\n[bold yellow]Session ended by user.[/bold yellow]")
            break
        except EOFError:
            console.print("\n[bold yellow]Session ended.[/bold yellow]")
            break


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
        secure_1psid, secure_1psidts = load_cookies()
    except CookieExpiredError as e:
        console.print(f"[bold red]Session expired:[/bold red] {e}")
        console.print("[bold yellow]Run 'webgemini auth' to re-authenticate.[/bold yellow]")
        sys.exit(2)
    except AuthenticationError as e:
        console.print(f"[bold red]Not authenticated:[/bold red] {e}")
        console.print("[bold yellow]Run 'webgemini auth' to authenticate.[/bold yellow]")
        sys.exit(2)

    try:
        client = GeminiClient(secure_1psid, secure_1psidts)
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
    else:
        output_path = Path(output_path)

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
        secure_1psid, secure_1psidts = load_cookies()
    except CookieExpiredError as e:
        console.print(f"[bold red]Session expired:[/bold red] {e}")
        console.print("[bold yellow]Run 'webgemini auth' to re-authenticate.[/bold yellow]")
        sys.exit(2)
    except AuthenticationError as e:
        console.print(f"[bold red]Not authenticated:[/bold red] {e}")
        console.print("[bold yellow]Run 'webgemini auth' to authenticate.[/bold yellow]")
        sys.exit(2)

    try:
        client = GeminiClient(secure_1psid, secure_1psidts)
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
        secure_1psid, secure_1psidts = load_cookies()
        client = GeminiClient(secure_1psid, secure_1psidts)
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
