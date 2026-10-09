"""Console presentation layer using Rich."""

import sys
from collections.abc import Sequence

from rich.console import Console


def _get_stdout_console() -> Console:
    return Console(file=sys.stdout, highlight=False, soft_wrap=True, width=400)


def _get_stderr_console() -> Console:
    return Console(file=sys.stderr, highlight=False, soft_wrap=True, width=400)


def print_message(message: str, quiet: bool = False, err: bool = False) -> None:
    """Print standard status message unless quiet mode is enabled."""
    if quiet:
        return
    console = _get_stderr_console() if err else _get_stdout_console()
    console.print(message)


def print_warning(warning: str, quiet: bool = False) -> None:
    """Print warning message to stderr."""
    if quiet:
        return
    _get_stderr_console().print(f"[yellow]Warning:[/yellow] {warning}")


def print_error(error_message: str) -> None:
    """Print error message to stderr."""
    _get_stderr_console().print(f"[bold red]Error:[/bold red] {error_message}")


def print_plan(
    plan_description: Sequence[str],
    output_path: str | None = None,
    quiet: bool = False,
) -> None:
    """Print human-readable composition plan."""
    if quiet:
        return
    console = _get_stdout_console()
    if output_path:
        console.print(f"[bold]Target Output:[/bold] {output_path}")
    console.print("[bold]Composition Plan:[/bold]")
    for line in plan_description:
        console.print(f"  {line}")
