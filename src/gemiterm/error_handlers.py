import sys

from rich.console import Console

from gemiterm.exceptions import (
    AuthenticationError,
    CookieExpiredError,
    GeminiAPIError,
)

console = Console()


def handle_cli_error(error: Exception) -> None:
    """Handle CLI errors with appropriate messages and exit codes."""
    if isinstance(error, CookieExpiredError):
        console.print(f"[bold red]Session expired:[/bold red] {error}")
        console.print("[bold yellow]Run 'gemiterm auth' to re-authenticate.[/bold yellow]")
        sys.exit(2)
    elif isinstance(error, AuthenticationError):
        console.print(f"[bold red]Not authenticated:[/bold red] {error}")
        console.print("[bold yellow]Run 'gemiterm auth' to authenticate.[/bold yellow]")
        sys.exit(2)
    elif isinstance(error, GeminiAPIError):
        console.print(f"[bold red]API error:[/bold red] {error}")
        sys.exit(1)


def require_active_profiles(statuses: list[dict]) -> list[str]:
    """Return active profile names or exit if none found."""
    active = [s["name"] for s in statuses if s["is_active"]]
    if not active:
        console.print("[bold red]No active profiles found.[/bold red]")
        console.print("[yellow]Run 'gemiterm auth' to authenticate.[/yellow]")
        sys.exit(2)
    return active
