"""Command-line interface for text-file-collector."""

from __future__ import annotations

import argparse
import codecs
import logging
import sys
from pathlib import Path
from typing import Sequence

from text_file_collector import __version__
from text_file_collector.collector import (
    DEFAULT_EXCLUDES,
    CollectionOptions,
    collect_text_files,
)
from text_file_collector.exceptions import TextFileCollectorError
from text_file_collector.logging_config import configure_logging

logger = logging.getLogger(__name__)

ALLOWED_LOG_LEVELS = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="text-file-collector",
        description="Recursively collect readable text files into one combined output file.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run", help="Collect text files from a directory.")
    run_parser.add_argument("--input-dir", required=True, type=Path, help="Directory to scan recursively.")
    run_parser.add_argument("--output-file", required=True, type=Path, help="Output text file.")
    run_parser.add_argument("--encoding", default="utf-8", help="Text encoding to read and write.")
    run_parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level: CRITICAL, ERROR, WARNING, INFO, or DEBUG.",
    )
    run_parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Exclude a file or directory name, relative path, or glob pattern. May be repeated.",
    )
    run_parser.add_argument(
        "--no-default-excludes",
        action="store_true",
        help="Disable built-in excludes for common project noise.",
    )

    return parser


def run_command(args: argparse.Namespace) -> int:
    """Execute the run subcommand."""
    log_level = str(args.log_level).upper()
    configure_logging(log_level if log_level in ALLOWED_LOG_LEVELS else "INFO")

    validation_error = validate_run_args(args, log_level)
    if validation_error is not None:
        print(f"Invalid command input: {validation_error}", file=sys.stderr)
        return 2

    excludes = tuple(args.exclude)
    if not args.no_default_excludes:
        excludes = DEFAULT_EXCLUDES + excludes

    options = CollectionOptions(
        input_dir=args.input_dir,
        output_file=args.output_file,
        encoding=args.encoding,
        excludes=excludes,
    )

    try:
        result = collect_text_files(options)
    except TextFileCollectorError as exc:
        logger.error("Collection failed: %s", exc)
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception:
        logger.exception("Unexpected failure.")
        print("Unexpected error. Run with --log-level DEBUG for details.", file=sys.stderr)
        return 99

    print(
        "Done. "
        f"Wrote {result.files_written} text file(s) to: {result.output_file}. "
        f"Skipped {result.files_skipped} file(s)."
    )
    return 0


def validate_run_args(args: argparse.Namespace, log_level: str) -> str | None:
    """Validate run arguments and return an error message when invalid."""
    input_dir = args.input_dir.expanduser()
    output_file = args.output_file.expanduser()

    if not input_dir.exists():
        return f"Input directory does not exist: {args.input_dir}"
    if not input_dir.is_dir():
        return f"Input path is not a directory: {args.input_dir}"
    if output_file.exists() and output_file.is_dir():
        return f"Output file is an existing directory: {args.output_file}"
    if log_level not in ALLOWED_LOG_LEVELS:
        return f"Unsupported log level: {args.log_level}"

    try:
        codecs.lookup(args.encoding)
    except LookupError:
        return f"Unsupported encoding: {args.encoding}"

    return None


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)

    if args.command == "run":
        return run_command(args)

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
