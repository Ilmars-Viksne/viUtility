"""Command-line interface for text-file-collector."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Sequence

from pydantic import BaseModel, Field, ValidationError, field_validator

from text_file_collector import __version__
from text_file_collector.composition import (
    build_collection_service,
    normalize_input_path,
    normalize_output_path,
)
from text_file_collector.config import load_settings
from text_file_collector.core.entities import CollectionRequest
from text_file_collector.core.exceptions import TextFileCollectorError
from text_file_collector.logging_config import configure_logging

logger = logging.getLogger(__name__)


class RunCommandInput(BaseModel):
    """Validated CLI input for the run command."""

    input_dir: Path = Field(description="Directory to scan recursively.")
    output_file: Path = Field(description="Output text file.")
    log_level: str = Field(default="INFO", description="Logging level.")

    @field_validator("input_dir")
    @classmethod
    def input_dir_must_exist(cls, value: Path) -> Path:
        expanded = value.expanduser()

        if not expanded.is_dir():
            raise ValueError(f"Input directory does not exist: {value}")

        return value

    @field_validator("output_file")
    @classmethod
    def output_file_parent_must_be_valid(cls, value: Path) -> Path:
        parent = value.expanduser().parent

        if parent.exists() and not parent.is_dir():
            raise ValueError(f"Output parent is not a directory: {parent}")

        return value

    @field_validator("log_level")
    @classmethod
    def log_level_must_be_supported(cls, value: str) -> str:
        normalized = value.upper()
        allowed = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}

        if normalized not in allowed:
            raise ValueError(f"Unsupported log level: {value}")

        return normalized


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="text-file-collector",
        description="Recursively collect non-binary text files into one combined output file.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser(
        "run",
        help="Collect non-binary files from a directory.",
    )
    run_parser.add_argument(
        "--input-dir",
        required=True,
        type=Path,
        help="Directory to scan recursively.",
    )
    run_parser.add_argument(
        "--output-file",
        required=True,
        type=Path,
        help="Output text file to create.",
    )
    run_parser.add_argument(
        "--log-level",
        default=None,
        help="Logging level: CRITICAL, ERROR, WARNING, INFO, or DEBUG.",
    )

    return parser


def run_command(args: argparse.Namespace) -> int:
    """Execute the run command."""
    settings = load_settings()
    requested_log_level = args.log_level or settings.log_level

    try:
        cli_input = RunCommandInput(
            input_dir=args.input_dir,
            output_file=args.output_file,
            log_level=requested_log_level,
        )
    except ValidationError as exc:
        configure_logging(requested_log_level)
        logger.error("CLI validation failed.")
        print("Invalid command input:", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 2

    configure_logging(cli_input.log_level)

    try:
        service = build_collection_service(settings)
        request = CollectionRequest(
            input_directory=normalize_input_path(cli_input.input_dir),
            output_file=normalize_output_path(cli_input.output_file),
        )

        result = service.collect(request)

        print(
            "Done. "
            f"Wrote {result.text_files_written} text file(s) to: {result.output_file}. "
            f"Skipped {result.binary_files_skipped} binary file(s)."
        )
        return 0
    except TextFileCollectorError as exc:
        logger.error("Collection failed: %s", exc)
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception:
        logger.exception("Unexpected failure.")
        print("Unexpected error. Run with --log-level DEBUG for details.", file=sys.stderr)
        return 99


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        return run_command(args)

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
