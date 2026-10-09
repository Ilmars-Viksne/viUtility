"""Main Typer CLI application for PDF File Collector."""

from pathlib import Path

import typer

from pdf_file_collector import __version__
from pdf_file_collector.commands.collect import (
    execute_append,
    execute_collect_or_compose,
    execute_insert,
    execute_merge,
    execute_plan,
    execute_prepend,
    execute_validate,
)
from pdf_file_collector.commands.extract import (
    execute_extract,
    execute_remove,
    execute_reorder,
    execute_reverse,
)
from pdf_file_collector.commands.info import execute_info
from pdf_file_collector.commands.split import execute_split
from pdf_file_collector.core.exceptions import ExitCode, PdfFileCollectorError
from pdf_file_collector.core.metadata import SingleSourceMetadataPolicy
from pdf_file_collector.presentation.console import print_error
from pdf_file_collector.presentation.json_output import format_json_error, print_json_stderr

app = typer.Typer(
    name="PDF File Collector",
    help="A non-destructive Python CLI for collecting, extracting, inserting, "
    "removing, reordering, reversing, splitting, merging, and composing pages from PDF files.",
    add_completion=False,
    no_args_is_help=True,
)

# Global options state flag
_json_mode = False


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"PDF File Collector {__version__}")
        raise typer.Exit(code=0)


@app.callback()
def main(
    version: bool | None = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """PDF File Collector entry point."""
    pass


def handle_error_and_exit(e: Exception, op_name: str, json_format: bool, debug: bool = False) -> None:
    if debug:
        import traceback

        traceback.print_exc()

    if isinstance(e, PdfFileCollectorError):
        code = e.exit_code
        err_type = type(e).__name__
        msg = str(e)
    elif isinstance(e, typer.Exit):
        raise e
    else:
        code = ExitCode.UNEXPECTED_FAILURE
        err_type = "UnexpectedError"
        msg = str(e) or "An unexpected error occurred."

    if json_format:
        err_obj = format_json_error(
            operation=op_name,
            error_code=int(code),
            error_type=err_type,
            message=msg,
        )
        print_json_stderr(err_obj)
    else:
        print_error(msg)

    raise typer.Exit(code=int(code))


@app.command("info")
def info_cmd(
    pdf_path: Path = typer.Argument(..., help="Path to source PDF file."),
    pages: str = typer.Option("all", "--pages", help="Page selection expression to inspect."),
    json_format: bool = typer.Option(False, "--json", help="Output in JSON format."),
    strict: bool = typer.Option(False, "--strict", help="Enable strict PDF parsing."),
    password: str | None = typer.Option(None, "--password", help="PDF password."),
    password_env: str | None = typer.Option(
        None, "--password-env", help="Environment variable containing PDF password."
    ),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output."),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress non-essential messages."),
    debug: bool = typer.Option(False, "--debug", help="Print debug tracebacks on error."),
) -> None:
    """Display PDF document information without modifying files."""
    try:
        execute_info(
            pdf_path=pdf_path,
            pages_expr=pages,
            json_format=json_format,
            strict=strict,
            password=password,
            password_env=password_env,
            quiet=quiet,
        )
    except Exception as e:
        handle_error_and_exit(e, "info", json_format, debug)


@app.command("extract")
def extract_cmd(
    source_path: Path = typer.Argument(..., help="Path to source PDF file."),
    pages: str = typer.Option(..., "--pages", help="Page selection expression (e.g. '1-3,8,last')."),
    output: Path = typer.Option(..., "--output", "-o", help="Output PDF file path."),
    unique: bool = typer.Option(False, "--unique", help="Deduplicate selected pages."),
    metadata: SingleSourceMetadataPolicy = typer.Option(
        SingleSourceMetadataPolicy.KEEP, "--metadata", help="Metadata policy ('keep' or 'drop')."
    ),
    strict: bool = typer.Option(False, "--strict", help="Enable strict PDF parsing."),
    password: str | None = typer.Option(None, "--password", help="PDF password."),
    password_env: str | None = typer.Option(
        None, "--password-env", help="Environment variable containing PDF password."
    ),
    overwrite_output: bool = typer.Option(False, "--overwrite-output", help="Allow replacing an existing output file."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate execution without writing files."),
    json_format: bool = typer.Option(False, "--json", help="Output in JSON format."),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output."),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress non-essential messages."),
    debug: bool = typer.Option(False, "--debug", help="Print debug tracebacks on error."),
) -> None:
    """Create a new PDF containing selected pages from source PDF."""
    try:
        execute_extract(
            source_path=source_path,
            pages_expr=pages,
            output_path=output,
            unique=unique,
            metadata_policy=metadata,
            strict=strict,
            password=password,
            password_env=password_env,
            overwrite_output=overwrite_output,
            dry_run=dry_run,
            json_format=json_format,
            quiet=quiet,
        )
    except Exception as e:
        handle_error_and_exit(e, "extract", json_format, debug)


@app.command("remove")
def remove_cmd(
    source_path: Path = typer.Argument(..., help="Path to source PDF file."),
    pages: str = typer.Option(..., "--pages", help="Pages to remove (e.g. '2,5-7')."),
    output: Path = typer.Option(..., "--output", "-o", help="Output PDF file path."),
    metadata: SingleSourceMetadataPolicy = typer.Option(
        SingleSourceMetadataPolicy.KEEP, "--metadata", help="Metadata policy ('keep' or 'drop')."
    ),
    strict: bool = typer.Option(False, "--strict", help="Enable strict PDF parsing."),
    password: str | None = typer.Option(None, "--password", help="PDF password."),
    password_env: str | None = typer.Option(
        None, "--password-env", help="Environment variable containing PDF password."
    ),
    overwrite_output: bool = typer.Option(False, "--overwrite-output", help="Allow replacing an existing output file."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate execution without writing files."),
    json_format: bool = typer.Option(False, "--json", help="Output in JSON format."),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output."),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress non-essential messages."),
    debug: bool = typer.Option(False, "--debug", help="Print debug tracebacks on error."),
) -> None:
    """Create a new PDF containing all pages except selected pages."""
    try:
        execute_remove(
            source_path=source_path,
            pages_expr=pages,
            output_path=output,
            metadata_policy=metadata,
            strict=strict,
            password=password,
            password_env=password_env,
            overwrite_output=overwrite_output,
            dry_run=dry_run,
            json_format=json_format,
            quiet=quiet,
        )
    except Exception as e:
        handle_error_and_exit(e, "remove", json_format, debug)


@app.command("reorder")
def reorder_cmd(
    source_path: Path = typer.Argument(..., help="Path to source PDF file."),
    pages: str = typer.Option(..., "--pages", help="Explicit page sequence (e.g. '3,1,2,4-last')."),
    output: Path = typer.Option(..., "--output", "-o", help="Output PDF file path."),
    unique: bool = typer.Option(False, "--unique", help="Deduplicate selected pages."),
    metadata: SingleSourceMetadataPolicy = typer.Option(
        SingleSourceMetadataPolicy.KEEP, "--metadata", help="Metadata policy ('keep' or 'drop')."
    ),
    strict: bool = typer.Option(False, "--strict", help="Enable strict PDF parsing."),
    password: str | None = typer.Option(None, "--password", help="PDF password."),
    password_env: str | None = typer.Option(
        None, "--password-env", help="Environment variable containing PDF password."
    ),
    overwrite_output: bool = typer.Option(False, "--overwrite-output", help="Allow replacing an existing output file."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate execution without writing files."),
    json_format: bool = typer.Option(False, "--json", help="Output in JSON format."),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output."),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress non-essential messages."),
    debug: bool = typer.Option(False, "--debug", help="Print debug tracebacks on error."),
) -> None:
    """Create a new PDF with pages in explicit requested sequence."""
    try:
        execute_reorder(
            source_path=source_path,
            pages_expr=pages,
            output_path=output,
            unique=unique,
            metadata_policy=metadata,
            strict=strict,
            password=password,
            password_env=password_env,
            overwrite_output=overwrite_output,
            dry_run=dry_run,
            json_format=json_format,
            quiet=quiet,
        )
    except Exception as e:
        handle_error_and_exit(e, "reorder", json_format, debug)


@app.command("reverse")
def reverse_cmd(
    source_path: Path = typer.Argument(..., help="Path to source PDF file."),
    output: Path = typer.Option(..., "--output", "-o", help="Output PDF file path."),
    pages: str | None = typer.Option(None, "--pages", help="Optional page selection to reverse."),
    metadata: SingleSourceMetadataPolicy = typer.Option(
        SingleSourceMetadataPolicy.KEEP, "--metadata", help="Metadata policy ('keep' or 'drop')."
    ),
    strict: bool = typer.Option(False, "--strict", help="Enable strict PDF parsing."),
    password: str | None = typer.Option(None, "--password", help="PDF password."),
    password_env: str | None = typer.Option(
        None, "--password-env", help="Environment variable containing PDF password."
    ),
    overwrite_output: bool = typer.Option(False, "--overwrite-output", help="Allow replacing an existing output file."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate execution without writing files."),
    json_format: bool = typer.Option(False, "--json", help="Output in JSON format."),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output."),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress non-essential messages."),
    debug: bool = typer.Option(False, "--debug", help="Print debug tracebacks on error."),
) -> None:
    """Create a new PDF with reversed page order."""
    try:
        execute_reverse(
            source_path=source_path,
            output_path=output,
            pages_expr=pages,
            metadata_policy=metadata,
            strict=strict,
            password=password,
            password_env=password_env,
            overwrite_output=overwrite_output,
            dry_run=dry_run,
            json_format=json_format,
            quiet=quiet,
        )
    except Exception as e:
        handle_error_and_exit(e, "reverse", json_format, debug)


@app.command("insert")
def insert_cmd(
    base_path: Path = typer.Argument(..., help="Path to base PDF file."),
    donor_path: Path = typer.Argument(..., help="Path to donor PDF file."),
    donor_pages: str = typer.Option(..., "--donor-pages", help="Donor pages to insert (e.g. '2-4')."),
    before: int | None = typer.Option(None, "--before", help="1-based page position to insert before."),
    after: str | None = typer.Option(None, "--after", help="1-based page position or 'last' to insert after."),
    output: Path = typer.Option(..., "--output", "-o", help="Output PDF file path."),
    strict: bool = typer.Option(False, "--strict", help="Enable strict PDF parsing."),
    password: str | None = typer.Option(None, "--password", help="PDF password."),
    password_env: str | None = typer.Option(
        None, "--password-env", help="Environment variable containing PDF password."
    ),
    overwrite_output: bool = typer.Option(False, "--overwrite-output", help="Allow replacing an existing output file."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate execution without writing files."),
    json_format: bool = typer.Option(False, "--json", help="Output in JSON format."),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output."),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress non-essential messages."),
    debug: bool = typer.Option(False, "--debug", help="Print debug tracebacks on error."),
) -> None:
    """Insert selected pages from donor PDF into base PDF."""
    try:
        execute_insert(
            base_path=base_path,
            donor_path=donor_path,
            donor_pages_expr=donor_pages,
            before_position=before,
            after_position=after,
            output_path=output,
            strict=strict,
            password=password,
            password_env=password_env,
            overwrite_output=overwrite_output,
            dry_run=dry_run,
            json_format=json_format,
            quiet=quiet,
        )
    except Exception as e:
        handle_error_and_exit(e, "insert", json_format, debug)


@app.command("append")
def append_cmd(
    base_path: Path = typer.Argument(..., help="Path to base PDF file."),
    adds: list[str] = typer.Option(..., "--add", help="Donor source specification 'PATH::PAGE_EXPRESSION'."),
    output: Path = typer.Option(..., "--output", "-o", help="Output PDF file path."),
    strict: bool = typer.Option(False, "--strict", help="Enable strict PDF parsing."),
    password: str | None = typer.Option(None, "--password", help="PDF password."),
    password_env: str | None = typer.Option(
        None, "--password-env", help="Environment variable containing PDF password."
    ),
    overwrite_output: bool = typer.Option(False, "--overwrite-output", help="Allow replacing an existing output file."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate execution without writing files."),
    json_format: bool = typer.Option(False, "--json", help="Output in JSON format."),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output."),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress non-essential messages."),
    debug: bool = typer.Option(False, "--debug", help="Print debug tracebacks on error."),
) -> None:
    """Append selected donor pages to end of base PDF."""
    try:
        execute_append(
            base_path=base_path,
            adds_raw=adds,
            output_path=output,
            strict=strict,
            password=password,
            password_env=password_env,
            overwrite_output=overwrite_output,
            dry_run=dry_run,
            json_format=json_format,
            quiet=quiet,
        )
    except Exception as e:
        handle_error_and_exit(e, "append", json_format, debug)


@app.command("prepend")
def prepend_cmd(
    base_path: Path = typer.Argument(..., help="Path to base PDF file."),
    adds: list[str] = typer.Option(..., "--add", help="Donor source specification 'PATH::PAGE_EXPRESSION'."),
    output: Path = typer.Option(..., "--output", "-o", help="Output PDF file path."),
    strict: bool = typer.Option(False, "--strict", help="Enable strict PDF parsing."),
    password: str | None = typer.Option(None, "--password", help="PDF password."),
    password_env: str | None = typer.Option(
        None, "--password-env", help="Environment variable containing PDF password."
    ),
    overwrite_output: bool = typer.Option(False, "--overwrite-output", help="Allow replacing an existing output file."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate execution without writing files."),
    json_format: bool = typer.Option(False, "--json", help="Output in JSON format."),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output."),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress non-essential messages."),
    debug: bool = typer.Option(False, "--debug", help="Print debug tracebacks on error."),
) -> None:
    """Prepend selected donor pages before base PDF."""
    try:
        execute_prepend(
            base_path=base_path,
            adds_raw=adds,
            output_path=output,
            strict=strict,
            password=password,
            password_env=password_env,
            overwrite_output=overwrite_output,
            dry_run=dry_run,
            json_format=json_format,
            quiet=quiet,
        )
    except Exception as e:
        handle_error_and_exit(e, "prepend", json_format, debug)


@app.command("merge")
def merge_cmd(
    positional_paths: list[Path] | None = typer.Argument(None, help="Positional PDF files to merge completely."),
    sources: list[str] | None = typer.Option(None, "--source", help="Source specification 'PATH::PAGE_EXPRESSION'."),
    output: Path = typer.Option(..., "--output", "-o", help="Output PDF file path."),
    strict: bool = typer.Option(False, "--strict", help="Enable strict PDF parsing."),
    password: str | None = typer.Option(None, "--password", help="PDF password."),
    password_env: str | None = typer.Option(
        None, "--password-env", help="Environment variable containing PDF password."
    ),
    overwrite_output: bool = typer.Option(False, "--overwrite-output", help="Allow replacing an existing output file."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate execution without writing files."),
    json_format: bool = typer.Option(False, "--json", help="Output in JSON format."),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output."),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress non-essential messages."),
    debug: bool = typer.Option(False, "--debug", help="Print debug tracebacks on error."),
) -> None:
    """Merge complete PDFs or selected page ranges."""
    try:
        execute_merge(
            positional_paths=positional_paths or [],
            sources_raw=sources or [],
            output_path=output,
            strict=strict,
            password=password,
            password_env=password_env,
            overwrite_output=overwrite_output,
            dry_run=dry_run,
            json_format=json_format,
            quiet=quiet,
        )
    except Exception as e:
        handle_error_and_exit(e, "merge", json_format, debug)


@app.command("split")
def split_cmd(
    source_path: Path = typer.Argument(..., help="Path to source PDF file."),
    output_dir: Path = typer.Option(..., "--output-dir", help="Directory for split outputs."),
    every: int | None = typer.Option(None, "--every", help="Split into chunks of N pages."),
    ranges: str | None = typer.Option(None, "--ranges", help="Semicolon-separated ranges (e.g. '1-3;4-8;9-last')."),
    at: str | None = typer.Option(None, "--at", help="Comma-separated split points (e.g. '5,10,25')."),
    strict: bool = typer.Option(False, "--strict", help="Enable strict PDF parsing."),
    password: str | None = typer.Option(None, "--password", help="PDF password."),
    password_env: str | None = typer.Option(
        None, "--password-env", help="Environment variable containing PDF password."
    ),
    overwrite_output: bool = typer.Option(False, "--overwrite-output", help="Allow replacing existing output files."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate execution without writing files."),
    json_format: bool = typer.Option(False, "--json", help="Output in JSON format."),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output."),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress non-essential messages."),
    debug: bool = typer.Option(False, "--debug", help="Print debug tracebacks on error."),
) -> None:
    """Split PDF by chunk size (--every), explicit ranges (--ranges), or split points (--at)."""
    try:
        execute_split(
            source_path=source_path,
            output_dir=output_dir,
            every=every,
            ranges_raw=ranges,
            at_raw=at,
            strict=strict,
            password=password,
            password_env=password_env,
            overwrite_output=overwrite_output,
            dry_run=dry_run,
            json_format=json_format,
            quiet=quiet,
        )
    except Exception as e:
        handle_error_and_exit(e, "split", json_format, debug)


@app.command("collect")
def collect_cmd(
    sources: list[str] = typer.Option(..., "--source", help="Source specification 'PATH::PAGE_EXPRESSION'."),
    output: Path = typer.Option(..., "--output", "-o", help="Output PDF file path."),
    metadata_from: Path | None = typer.Option(None, "--metadata-from", help="Source path to preserve metadata from."),
    strict: bool = typer.Option(False, "--strict", help="Enable strict PDF parsing."),
    password: str | None = typer.Option(None, "--password", help="PDF password."),
    password_env: str | None = typer.Option(
        None, "--password-env", help="Environment variable containing PDF password."
    ),
    overwrite_output: bool = typer.Option(False, "--overwrite-output", help="Allow replacing an existing output file."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate execution without writing files."),
    json_format: bool = typer.Option(False, "--json", help="Output in JSON format."),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output."),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress non-essential messages."),
    debug: bool = typer.Option(False, "--debug", help="Print debug tracebacks on error."),
) -> None:
    """Collect pages from multiple source specifications into a new PDF."""
    try:
        execute_collect_or_compose(
            sources_raw=sources,
            output_path=output,
            metadata_from=metadata_from,
            strict=strict,
            password=password,
            password_env=password_env,
            overwrite_output=overwrite_output,
            dry_run=dry_run,
            json_format=json_format,
            quiet=quiet,
            command_name="collect",
        )
    except Exception as e:
        handle_error_and_exit(e, "collect", json_format, debug)


@app.command("compose")
def compose_cmd(
    sources: list[str] = typer.Option(..., "--source", help="Source specification 'PATH::PAGE_EXPRESSION'."),
    output: Path = typer.Option(..., "--output", "-o", help="Output PDF file path."),
    metadata_from: Path | None = typer.Option(None, "--metadata-from", help="Source path to preserve metadata from."),
    strict: bool = typer.Option(False, "--strict", help="Enable strict PDF parsing."),
    password: str | None = typer.Option(None, "--password", help="PDF password."),
    password_env: str | None = typer.Option(
        None, "--password-env", help="Environment variable containing PDF password."
    ),
    overwrite_output: bool = typer.Option(False, "--overwrite-output", help="Allow replacing an existing output file."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate execution without writing files."),
    json_format: bool = typer.Option(False, "--json", help="Output in JSON format."),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output."),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress non-essential messages."),
    debug: bool = typer.Option(False, "--debug", help="Print debug tracebacks on error."),
) -> None:
    """Alias for collect: compose pages from multiple source specifications into a new PDF."""
    try:
        execute_collect_or_compose(
            sources_raw=sources,
            output_path=output,
            metadata_from=metadata_from,
            strict=strict,
            password=password,
            password_env=password_env,
            overwrite_output=overwrite_output,
            dry_run=dry_run,
            json_format=json_format,
            quiet=quiet,
            command_name="compose",
        )
    except Exception as e:
        handle_error_and_exit(e, "compose", json_format, debug)


@app.command("validate")
def validate_cmd(
    source_path: Path | None = typer.Argument(None, help="Optional single input PDF path."),
    pages: str | None = typer.Option(None, "--pages", help="Page selection for single PDF."),
    sources: list[str] | None = typer.Option(None, "--source", help="Source specification 'PATH::PAGE_EXPRESSION'."),
    strict: bool = typer.Option(False, "--strict", help="Enable strict PDF parsing."),
    password: str | None = typer.Option(None, "--password", help="PDF password."),
    password_env: str | None = typer.Option(
        None, "--password-env", help="Environment variable containing PDF password."
    ),
    json_format: bool = typer.Option(False, "--json", help="Output in JSON format."),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output."),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress non-essential messages."),
    debug: bool = typer.Option(False, "--debug", help="Print debug tracebacks on error."),
) -> None:
    """Validate PDF inputs and page selections without writing output."""
    try:
        execute_validate(
            positional_path=source_path,
            pages_expr=pages,
            sources_raw=sources or [],
            strict=strict,
            password=password,
            password_env=password_env,
            json_format=json_format,
            quiet=quiet,
        )
    except Exception as e:
        handle_error_and_exit(e, "validate", json_format, debug)


@app.command("plan")
def plan_cmd(
    sources: list[str] = typer.Option(..., "--source", help="Source specification 'PATH::PAGE_EXPRESSION'."),
    output: Path | None = typer.Option(None, "--output", "-o", help="Optional target output PDF path."),
    strict: bool = typer.Option(False, "--strict", help="Enable strict PDF parsing."),
    password: str | None = typer.Option(None, "--password", help="PDF password."),
    password_env: str | None = typer.Option(
        None, "--password-env", help="Environment variable containing PDF password."
    ),
    json_format: bool = typer.Option(False, "--json", help="Output in JSON format."),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output."),
    quiet: bool = typer.Option(False, "--quiet", help="Suppress non-essential messages."),
    debug: bool = typer.Option(False, "--debug", help="Print debug tracebacks on error."),
) -> None:
    """Display exact page collection plan without writing output."""
    try:
        execute_plan(
            sources_raw=sources,
            output_path=output,
            strict=strict,
            password=password,
            password_env=password_env,
            json_format=json_format,
            quiet=quiet,
        )
    except Exception as e:
        handle_error_and_exit(e, "plan", json_format, debug)


if __name__ == "__main__":
    app()
