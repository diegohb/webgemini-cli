import sys
from datetime import datetime

from rich.console import Console

console = Console()


def validate_conversation_id(conversation_id: str) -> None:
    """Exit with error if conversation_id is empty or whitespace."""
    if not conversation_id or not conversation_id.strip():
        console.print("[bold red]Error:[/bold red] conversation_id cannot be empty.")
        sys.exit(1)


def parse_iso_date(date_str: str, field_name: str) -> float:
    """Parse an ISO date string into a timestamp, or exit with error."""
    try:
        return datetime.fromisoformat(date_str).timestamp()
    except ValueError:
        console.print(
            f"[bold red]Error:[/bold red] Invalid date format for --{field_name}."
            f" Use ISO format (e.g., 2024-01-01)."
        )
        sys.exit(1)
