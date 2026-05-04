import asyncio
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from gemiterm import __version__
from gemiterm.auth_manager import (
    delete_profile,
    get_default_profile_name,
    list_profile_statuses,
    list_profiles,
    load_cookies,
    login,
    rename_profile,
)
from gemiterm.exceptions import (
    AuthenticationError,
    CookieExpiredError,
    ConversationNotFoundError,
    GeminiAPIError,
)
from gemiterm.gemini_client import GeminiClient
from gemiterm.logging_config import setup_logging

console = Console()


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose logging")
@click.version_option(version=__version__, prog_name="gemiterm")
def cli(verbose: bool) -> None:
    if verbose:
        setup_logging(verbose=True)


@cli.command()
def auth() -> None:
    profiles = list_profiles()
    if not profiles:
        console.print("[bold blue]No profiles found. Creating default profile...[/bold blue]")
        try:
            asyncio.run(login())
            console.print(
                "[bold green]Authentication successful! Created 'default' profile.[/bold green]"
            )
        except Exception as e:
            console.print(f"[bold red]Authentication failed:[/bold red] {e}")
            sys.exit(1)
    else:
        show_auth_menu()


def show_auth_menu() -> None:
    statuses = list_profile_statuses()
    default_name = get_default_profile_name()

    table = Table(title="Authentication Profiles")
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="yellow")
    table.add_column("Expires", style="blue")
    table.add_column("Default", style="green")

    for status in statuses:
        name = status["name"]
        if status["is_active"]:
            status_str = "Active"
        elif status["exists"]:
            status_str = "Refresh needed"
        else:
            status_str = "Expired"
        expires = status.get("expires_at") or "N/A"
        default_marker = "*" if name == default_name else ""
        table.add_row(name, status_str, expires, default_marker)

    console.print(table)
    console.print()
    console.print("[bold]Select an action:[/bold]")
    console.print("  [A] Add new profile")
    console.print("  [D] Delete profile")
    console.print("  [S] Set default")
    console.print("  [R] Rename profile")
    console.print("  [X] Exit and continue with current default")

    try:
        choice = console.input("\nEnter choice (A/D/S/R/X): ").strip().upper()

        if choice == "A":
            new_name = click.prompt("Enter new profile name")
            try:
                asyncio.run(login(new_name))
                console.print(f"[bold green]Profile '{new_name}' created successfully![/bold green]")
            except Exception as e:
                console.print(f"[bold red]Authentication failed:[/bold red] {e}")
                sys.exit(1)
        elif choice == "D":
            name_to_delete = click.prompt("Enter profile name to delete")
            if name_to_delete == default_name:
                console.print("[bold yellow]Cannot delete the default profile.[/bold yellow]")
                return
            confirm = console.input(f"Delete profile '{name_to_delete}'? (yes/no): ").strip().lower()
            if confirm == "yes":
                delete_profile(name_to_delete)
                console.print(f"[bold green]Profile '{name_to_delete}' deleted.[/bold green]")
        elif choice == "S":
            from gemiterm.config import set_default_profile_name

            name_to_set = click.prompt("Enter profile name to set as default")
            set_default_profile_name(name_to_set)
            console.print(f"[bold green]Default profile set to '{name_to_set}'.[/bold green]")
        elif choice == "R":
            old_name = click.prompt("Enter current profile name")
            new_name = click.prompt("Enter new profile name")
            rename_profile(old_name, new_name)
            console.print(
                f"[bold green]Profile renamed from '{old_name}' to '{new_name}'.[/bold green]"
            )
        elif choice == "X":
            console.print(f"Continuing with default profile: [cyan]{default_name}[/cyan]")
        else:
            console.print("[bold red]Invalid choice.[/bold red]")
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Exiting auth menu...[/bold yellow]")


@cli.command()
@click.argument("action", type=click.Choice(["add", "delete", "rename", "default", "list"]))
@click.argument("profile_name", required=False)
@click.argument("new_name", required=False)
def profile(action: str, profile_name: str | None, new_name: str | None) -> None:
    if action == "add":
        if not profile_name:
            profile_name = click.prompt("Enter new profile name")
        try:
            asyncio.run(login(profile_name))
            console.print(
                f"[bold green]Profile '{profile_name}' created successfully![/bold green]"
            )
        except Exception as e:
            console.print(f"[bold red]Authentication failed:[/bold red] {e}")
            sys.exit(1)
    elif action == "delete":
        if not profile_name:
            profile_name = click.prompt("Enter profile name to delete")
        default_name = get_default_profile_name()
        if profile_name == default_name:
            console.print("[bold yellow]Cannot delete the default profile.[/bold yellow]")
            return
        confirm = console.input(f"Delete profile '{profile_name}'? (yes/no): ").strip().lower()
        if confirm == "yes":
            delete_profile(profile_name)
            console.print(f"[bold green]Profile '{profile_name}' deleted.[/bold green]")
    elif action == "rename":
        statuses = list_profile_statuses()
        default_name = get_default_profile_name()
        table = Table(title="Profiles")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="yellow")
        table.add_column("Expires", style="blue")
        table.add_column("Default", style="green")
        for idx, status in enumerate(statuses, start=1):
            name = status["name"]
            if status["is_active"]:
                status_str = "Active"
            elif status["exists"]:
                status_str = "Refresh needed"
            else:
                status_str = "Expired"
            expires = status.get("expires_at") or "N/A"
            default_marker = "*" if name == default_name else ""
            table.add_row(str(idx), name, status_str, expires, default_marker)
        console.print(table)
        if not profile_name:
            profile_name = click.prompt("Enter profile ID to rename", type=int)
        if profile_name < 1 or profile_name > len(statuses):
            console.print("[bold red]Invalid profile ID.[/bold red]")
            return
        old_name = statuses[profile_name - 1]["name"]
        if not new_name:
            new_name = click.prompt("Enter new profile name")
        rename_profile(old_name, new_name)
        console.print(
            f"[bold green]Profile renamed from '{old_name}' to '{new_name}'.[/bold green]"
        )
    elif action == "default":
        if not profile_name:
            profile_name = click.prompt("Enter profile name to set as default")
        from gemiterm.config import set_default_profile_name

        set_default_profile_name(profile_name)
        console.print(f"[bold green]Default profile set to '{profile_name}'.[/bold green]")
    elif action == "list":
        statuses = list_profile_statuses()
        default_name = get_default_profile_name()
        table = Table(title="Profiles")
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="yellow")
        table.add_column("Expires", style="blue")
        table.add_column("Default", style="green")
        for status in statuses:
            name = status["name"]
            if status["is_active"]:
                status_str = "Active"
            elif status["exists"]:
                status_str = "Refresh needed"
            else:
                status_str = "Expired"
            expires = status.get("expires_at") or "N/A"
            default_marker = "*" if name == default_name else ""
            table.add_row(name, status_str, expires, default_marker)
        console.print(table)


@cli.command()
@click.option("-n", "--limit", default=10, help="Number of chats to display (default: 10)")
@click.option("-o", "--offset", default=0, help="Offset for pagination")
@click.option("--all", "fetch_all", is_flag=True, help="Fetch all cached chats")
@click.option(
    "-a", "--all-profiles", "all_profiles", is_flag=True, help="Operate across all active profiles"
)
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
    all_profiles: bool,
    sort: str,
    search: str | None,
    after: str | None,
    before: str | None,
) -> None:
    if limit < 1:
        limit = 1

    if all_profiles:
        statuses = list_profile_statuses()
        active_profiles = [s for s in statuses if s["is_active"]]
        if not active_profiles:
            console.print("[bold red]No active profiles found.[/bold red]")
            console.print("[yellow]Run 'gemiterm auth' to authenticate.[/yellow]")
            sys.exit(2)

        all_chats: dict[str, dict] = {}
        for profile_status in active_profiles:
            profile_name = profile_status["name"]
            try:
                secure_1psid, secure_1psidts = load_cookies(profile_name)
                client = GeminiClient(secure_1psid, secure_1psidts)
                chats = client.list_chats()
                for chat in chats:
                    chat["profile"] = profile_name
                    all_chats[chat["id"]] = chat
            except Exception:
                continue

        chats = list(all_chats.values())
    else:
        try:
            secure_1psid, secure_1psidts = load_cookies()
        except CookieExpiredError as e:
            console.print(f"[bold red]Session expired:[/bold red] {e}")
            console.print("[bold yellow]Run 'gemiterm auth' to re-authenticate.[/bold yellow]")
            sys.exit(2)
        except AuthenticationError as e:
            console.print(f"[bold red]Not authenticated:[/bold red] {e}")
            console.print("[bold yellow]Run 'gemiterm auth' to authenticate.[/bold yellow]")
            sys.exit(2)

        try:
            client = GeminiClient(secure_1psid, secure_1psidts)
            chats = client.list_chats()
        except CookieExpiredError as e:
            console.print(f"[bold red]Session expired:[/bold red] {e}")
            console.print("[bold yellow]Run 'gemiterm auth' to re-authenticate.[/bold yellow]")
            sys.exit(2)
        except AuthenticationError as e:
            console.print(f"[bold red]Authentication error:[/bold red] {e}")
            console.print("[bold yellow]Run 'gemiterm auth' to re-authenticate.[/bold yellow]")
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
    if all_profiles:
        table.add_column("Profile", style="magenta")

    for chat in paginated_chats:
        pin_marker = "*" if chat.get("is_pinned") else ""
        ts = chat.get("timestamp")
        date_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M") if ts else "N/A"
        if all_profiles:
            profile_name = chat.get("profile", "unknown")
            table.add_row(chat["id"], chat["title"], pin_marker, date_str, profile_name)
        else:
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

    statuses = list_profile_statuses()
    active_profiles = [s["name"] for s in statuses if s["is_active"]]
    if not active_profiles:
        console.print("[bold red]No active profiles found.[/bold red]")
        console.print("[yellow]Run 'gemiterm auth' to authenticate.[/yellow]")
        sys.exit(2)

    messages = None
    last_error = None
    for profile_name in active_profiles:
        try:
            secure_1psid, secure_1psidts = load_cookies(profile_name)
            client = GeminiClient(secure_1psid, secure_1psidts)
            messages = client.fetch_chat(conversation_id)
            break
        except ConversationNotFoundError:
            continue
        except CookieExpiredError as e:
            last_error = e
            continue
        except AuthenticationError as e:
            last_error = e
            continue
        except GeminiAPIError as e:
            last_error = e
            continue

    if messages is None:
        if last_error:
            console.print(f"[bold red]Failed to fetch conversation:[/bold red] {last_error}")
        console.print(
            "[bold yellow]Run 'gemiterm list' to see available conversations.[/bold yellow]"
        )
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

    statuses = list_profile_statuses()
    active_profiles = [s["name"] for s in statuses if s["is_active"]]
    if not active_profiles:
        console.print("[bold red]No active profiles found.[/bold red]")
        console.print("[yellow]Run 'gemiterm auth' to authenticate.[/bold yellow]")
        sys.exit(2)

    secure_1psid = None
    secure_1psidts = None
    for profile_name in active_profiles:
        try:
            secure_1psid, secure_1psidts = load_cookies(profile_name)
            client = GeminiClient(secure_1psid, secure_1psidts)
            client.continue_chat(conversation_id, "ping")
            break
        except (ConversationNotFoundError, CookieExpiredError, AuthenticationError):
            continue
        except GeminiAPIError:
            break

    if secure_1psid is None:
        console.print("[bold red]Conversation not found in any active profile.[/bold red]")
        console.print(
            "[bold yellow]Run 'gemiterm list' to see available conversations.[/bold yellow]"
        )
        sys.exit(1)

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
            "[bold yellow]Run 'gemiterm list' to see available conversations.[/bold yellow]"
        )
        sys.exit(1)
    except CookieExpiredError as e:
        console.print(f"[bold red]Session expired:[/bold red] {e}")
        console.print("[bold yellow]Run 'gemiterm auth' to re-authenticate.[/bold yellow]")
        sys.exit(2)
    except AuthenticationError as e:
        console.print(f"[bold red]Authentication error:[/bold red] {e}")
        console.print("[bold yellow]Run 'gemiterm auth' to re-authenticate.[/bold yellow]")
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

    console.print("[bold cyan]Interactive chat session started.[/bold cyan]")
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
                    "[bold yellow]Run 'gemiterm list' to see available conversations.[/bold yellow]"
                )
                break
            except CookieExpiredError as e:
                console.print(f"[bold red]Session expired:[/bold red] {e}")
                console.print("[bold yellow]Run 'gemiterm auth' to re-authenticate.[/bold yellow]")
                break
            except AuthenticationError as e:
                console.print(f"[bold red]Authentication error:[/bold red] {e}")
                console.print("[bold yellow]Run 'gemiterm auth' to re-authenticate.[/bold yellow]")
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
        console.print("[bold yellow]Run 'gemiterm auth' to re-authenticate.[/bold yellow]")
        sys.exit(2)
    except AuthenticationError as e:
        console.print(f"[bold red]Not authenticated:[/bold red] {e}")
        console.print("[bold yellow]Run 'gemiterm auth' to authenticate.[/bold yellow]")
        sys.exit(2)

    try:
        client = GeminiClient(secure_1psid, secure_1psidts)
        messages = client.fetch_chat(conversation_id)
    except ConversationNotFoundError as e:
        console.print(f"[bold red]Conversation not found:[/bold red] {e}")
        console.print(
            "[bold yellow]Run 'gemiterm list' to see available conversations.[/bold yellow]"
        )
        sys.exit(1)
    except CookieExpiredError as e:
        console.print(f"[bold red]Session expired:[/bold red] {e}")
        console.print("[bold yellow]Run 'gemiterm auth' to re-authenticate.[/bold yellow]")
        sys.exit(2)
    except AuthenticationError as e:
        console.print(f"[bold red]Authentication error:[/bold red] {e}")
        console.print("[bold yellow]Run 'gemiterm auth' to re-authenticate.[/bold yellow]")
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
        from gemiterm.exporter import format_chat_as_markdown

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
@click.option(
    "-a",
    "--all-profiles",
    "all_profiles",
    is_flag=True,
    help="Export from all active profiles",
)
def export_all(
    output_dir: Path | None, since: str | None, include_metadata: bool, all_profiles: bool
) -> None:
    if output_dir is None:
        output_dir = Path.cwd() / "exports"

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    from gemiterm.exporter import format_chat_as_markdown

    exported_chats: list[dict[str, str]] = []
    failed_chats: list[tuple[str, str]] = []

    if all_profiles:
        statuses = list_profile_statuses()
        active_profiles = [s for s in statuses if s["is_active"]]
        if not active_profiles:
            console.print("[bold red]No active profiles found.[/bold red]")
            console.print("[yellow]Run 'gemiterm auth' to authenticate.[/bold yellow]")
            sys.exit(2)

        all_chats_dict: dict[str, dict] = {}
        for profile_status in active_profiles:
            profile_name = profile_status["name"]
            try:
                secure_1psid, secure_1psidts = load_cookies(profile_name)
                client = GeminiClient(secure_1psid, secure_1psidts)
                chats = client.list_chats()
                for chat in chats:
                    chat["profile"] = profile_name
                    all_chats_dict[chat["id"]] = chat
            except Exception:
                continue
        all_chats = list(all_chats_dict.values())
    else:
        try:
            secure_1psid, secure_1psidts = load_cookies()
        except CookieExpiredError as e:
            console.print(f"[bold red]Session expired:[/bold red] {e}")
            console.print("[bold yellow]Run 'gemiterm auth' to re-authenticate.[/bold yellow]")
            sys.exit(2)
        except AuthenticationError as e:
            console.print(f"[bold red]Not authenticated:[/bold red] {e}")
            console.print("[bold yellow]Run 'gemiterm auth' to authenticate.[/bold yellow]")
            sys.exit(2)

        try:
            client = GeminiClient(secure_1psid, secure_1psidts)
            all_chats = client.list_chats()
        except CookieExpiredError as e:
            console.print(f"[bold red]Session expired:[/bold red] {e}")
            console.print("[bold yellow]Run 'gemiterm auth' to re-authenticate.[/bold yellow]")
            sys.exit(2)
        except AuthenticationError as e:
            console.print(f"[bold red]Authentication error:[/bold red] {e}")
            console.print("[bold yellow]Run 'gemiterm auth' to re-authenticate.[/bold yellow]")
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
            profile_name = chat.get("profile")

            progress.update(export_task, description=f"[cyan]Exporting: {title[:30]}...")

            try:
                if all_profiles and profile_name:
                    secure_1psid, secure_1psidts = load_cookies(profile_name)
                    client = GeminiClient(secure_1psid, secure_1psidts)
                messages = client.fetch_chat(conversation_id)
                if not messages:
                    progress.advance(export_task)
                    continue

                safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title)[:50]
                date_str = datetime.now().strftime("%Y%m%d")
                profile_suffix = f"-{profile_name}" if profile_name else ""
                filename = (
                    f"gemini-chat-{conversation_id}{profile_suffix}-{safe_title[:20]}-{date_str}.md"
                )
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


@cli.command("install-browser", hidden=True)
def install_browser() -> None:
    """Install Playwright Chromium browser."""
    console.print("[bold cyan]Installing Chromium browser...[/bold cyan]")

    if getattr(sys, "frozen", False):
        py_cmd = shutil.which("py")
        if py_cmd:
            result = subprocess.run([py_cmd, "-3", "--version"], capture_output=True, text=True)
            if (
                result.returncode == 0
                and "Python" in result.stdout
                and "not found" not in result.stdout.lower()
            ):
                cmd = [py_cmd, "-3", "-m", "playwright", "install", "chromium"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    console.print("[bold green]Chromium installed successfully.[/bold green]")
                    return
                console.print(
                    f"[yellow]py -3 method failed: {result.stderr or result.stdout}[/yellow]"
                )

        python_exe = shutil.which("python") or shutil.which("python3")
        if python_exe:
            result = subprocess.run([python_exe, "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                cmd = [python_exe, "-m", "playwright", "install", "chromium"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    console.print("[bold green]Chromium installed successfully.[/bold green]")
                    return
                console.print(
                    f"[yellow]python method failed: {result.stderr or result.stdout}[/yellow]"
                )

        console.print("[yellow]Attempting direct Chromium download...[/yellow]")
        _download_chromium_fallback()
        console.print("[bold green]Chromium installed successfully.[/bold green]")
    else:
        cmd = [sys.executable, "-m", "playwright", "install", "chromium"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            console.print("[bold red]Failed to install Chromium:[/bold red]")
            console.print(result.stderr)
            raise click.ClickException("Chromium installation failed")
        console.print("[bold green]Chromium installed successfully.[/bold green]")


def _check_existing_browser() -> bool:
    """Check if Edge or Chrome is available as a fallback browser."""
    from pathlib import Path

    edge_paths = [
        Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
        Path("C:/Program Files/Microsoft/Edge/Application/msedge.exe"),
        Path(os.path.expandvars("%ProgramFiles(x86)%/Microsoft/Edge/Application/msedge.exe")),
        Path(os.path.expandvars("%ProgramFiles%/Microsoft/Edge/Application/msedge.exe")),
    ]
    for edge_path in edge_paths:
        if edge_path.exists():
            console.print(f"[green]Found Edge at {edge_path}[/green]")
            return True

    chrome_paths = [
        Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
        Path(os.path.expandvars("%ProgramFiles%/Google/Chrome/Application/chrome.exe")),
        Path(os.path.expanduser("~/AppData/Local/Google/Chrome/Application/chrome.exe")),
    ]
    for chrome_path in chrome_paths:
        if chrome_path.exists():
            console.print(f"[green]Found Chrome at {chrome_path}[/green]")
            return True

    return False


def _download_chromium_fallback() -> None:
    """Download Chromium directly using PowerShell when Python is not available."""
    import zipfile
    import shutil as sh
    from pathlib import Path

    playwright_dir = Path.home() / ".cache" / "ms-playwright"
    chromium_base = playwright_dir / "chromium-1312"
    chrome_exe = chromium_base / "chrome-win" / "chrome.exe"

    if chrome_exe.exists():
        return

    if _check_existing_browser():
        console.print("[yellow]Using system Edge/Chrome instead of downloading Chromium.[/yellow]")
        return

    console.print("[cyan]No Edge or Chrome found. Downloading Chromium (~200MB)...[/cyan]")

    tmp_dir = playwright_dir / "tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    zip_path = tmp_dir / "chromium.zip"

    urls = [
        "https://playwright.azureedge.net/builds/chromium/1312/chrome-win.zip",
        "https://playwright.downloads.microsoft.com/download/chromium/1312/chrome-win.zip",
        "https://storage.googleapis.com/chromium-browser-snapshots/Win_x64/1312/chrome-win.zip",
    ]

    for url in urls:
        console.print(f"[cyan]Trying {url}...[/cyan]")
        ps_script = f'''
        $ProgressPreference = 'SilentlyContinue'
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri "{url}" -OutFile "{zip_path}" -UseBasicParsing
        '''
        result = subprocess.run(
            ["powershell", "-Command", ps_script], capture_output=True, text=True, timeout=300
        )
        if result.returncode == 0:
            try:
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(playwright_dir)
                sh.rmtree(tmp_dir, ignore_errors=True)
                console.print("[green]Chromium downloaded successfully.[/green]")
                return
            except Exception as e:
                console.print(f"[yellow]Extraction failed: {e}[/yellow]")
                continue

    sh.rmtree(tmp_dir, ignore_errors=True)
    raise RuntimeError("Failed to download Chromium from all sources")


@cli.command()
def status() -> None:
    from gemiterm.config import _get_config_dir

    config_dir = _get_config_dir()

    console.print("[bold]gemiterm Status[/bold]")
    console.print()
    console.print(f"Config directory: [cyan]{config_dir}[/cyan]")
    console.print()

    statuses = list_profile_statuses()
    if not statuses:
        console.print("[bold red]Status: No profiles found[/bold red]")
        console.print("[yellow]Run 'gemiterm auth' to create your first profile.[/yellow]")
        sys.exit(2)

    table = Table(title="Profiles")
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="yellow")
    table.add_column("Expires", style="blue")
    table.add_column("Default", style="green")

    default_name = get_default_profile_name()
    for status in statuses:
        name = status["name"]
        if status["is_active"]:
            status_str = "Active"
        elif status["exists"]:
            status_str = "Refresh needed"
        else:
            status_str = "Expired"
        expires = status.get("expires_at") or "N/A"
        default_marker = "*" if name == default_name else ""
        table.add_row(name, status_str, expires, default_marker)

    console.print(table)
