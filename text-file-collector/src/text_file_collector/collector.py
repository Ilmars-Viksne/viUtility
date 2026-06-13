"""Text file collection logic."""

from __future__ import annotations

import fnmatch
import logging
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from text_file_collector.exceptions import TextFileCollectorError

logger = logging.getLogger(__name__)

BINARY_CHECK_BYTES = 4096

DEFAULT_EXCLUDES = (
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".nox",
    ".idea",
    ".vscode",
    "node_modules",
    "dist",
    "build",
    "*.egg-info",
)


@dataclass(frozen=True)
class CollectionOptions:
    """Options for collecting text files."""

    input_dir: Path
    output_file: Path
    encoding: str = "utf-8"
    separator_length: int = 80
    excludes: tuple[str, ...] = DEFAULT_EXCLUDES


@dataclass(frozen=True)
class CollectionResult:
    """Summary of a collection run."""

    files_seen: int
    files_written: int
    files_skipped: int
    binary_files_skipped: int
    decode_errors_skipped: int
    read_errors_skipped: int
    output_file: Path


def collect_text_files(options: CollectionOptions) -> CollectionResult:
    """Collect readable text files into one output file."""
    input_dir = options.input_dir.expanduser().resolve()
    output_file = options.output_file.expanduser().resolve()

    if not input_dir.exists():
        raise TextFileCollectorError(f"Input directory does not exist: {options.input_dir}")
    if not input_dir.is_dir():
        raise TextFileCollectorError(f"Input path is not a directory: {options.input_dir}")
    if output_file.exists() and output_file.is_dir():
        raise TextFileCollectorError(f"Output file is an existing directory: {options.output_file}")

    output_file.parent.mkdir(parents=True, exist_ok=True)

    counts = {
        "files_seen": 0,
        "files_written": 0,
        "binary_files_skipped": 0,
        "decode_errors_skipped": 0,
        "read_errors_skipped": 0,
    }
    separator = "=" * options.separator_length
    temp_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding=options.encoding,
            newline="",
            dir=output_file.parent,
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name).resolve()

            for file_path, relative_path in iter_candidate_files(
                input_dir,
                output_file,
                temp_path,
                options.excludes,
            ):
                counts["files_seen"] += 1

                binary_result = is_binary_file(file_path)
                if binary_result is True:
                    counts["binary_files_skipped"] += 1
                    logger.debug("Skipping binary file: %s", relative_path)
                    continue
                if binary_result is None:
                    counts["read_errors_skipped"] += 1
                    logger.warning("Skipping unreadable file during binary check: %s", relative_path)
                    continue

                try:
                    content = file_path.read_text(encoding=options.encoding)
                except UnicodeDecodeError:
                    counts["decode_errors_skipped"] += 1
                    logger.warning("Skipping undecodable file: %s", relative_path)
                    continue
                except OSError as exc:
                    counts["read_errors_skipped"] += 1
                    logger.warning("Skipping unreadable file: %s (%s)", relative_path, exc)
                    continue

                temp_file.write(format_section(relative_path, content, separator))
                counts["files_written"] += 1

        temp_path.replace(output_file)
    except TextFileCollectorError:
        _cleanup_temp_file(temp_path)
        raise
    except OSError as exc:
        _cleanup_temp_file(temp_path)
        raise TextFileCollectorError(f"Failed to write output file: {output_file}") from exc
    except Exception:
        _cleanup_temp_file(temp_path)
        raise

    files_skipped = (
        counts["binary_files_skipped"]
        + counts["decode_errors_skipped"]
        + counts["read_errors_skipped"]
    )

    return CollectionResult(
        files_seen=counts["files_seen"],
        files_written=counts["files_written"],
        files_skipped=files_skipped,
        binary_files_skipped=counts["binary_files_skipped"],
        decode_errors_skipped=counts["decode_errors_skipped"],
        read_errors_skipped=counts["read_errors_skipped"],
        output_file=output_file,
    )


def iter_candidate_files(
    input_dir: Path,
    output_file: Path,
    temp_path: Path | None,
    excludes: Iterable[str],
) -> Iterable[tuple[Path, str]]:
    """Yield candidate files in deterministic order."""
    exclude_patterns = tuple(excludes)

    for current_root, dir_names, file_names in os.walk(input_dir):
        root_path = Path(current_root)
        relative_root = root_path.relative_to(input_dir)

        dir_names[:] = sorted(
            dir_name
            for dir_name in dir_names
            if not should_exclude(relative_root / dir_name, dir_name, exclude_patterns)
        )

        for file_name in sorted(file_names):
            file_path = root_path / file_name
            relative_path = file_path.relative_to(input_dir)
            relative_posix = relative_path.as_posix()

            if should_exclude(relative_path, file_name, exclude_patterns):
                continue
            if _same_path(file_path, output_file):
                continue
            if temp_path is not None and _same_path(file_path, temp_path):
                continue

            yield file_path, relative_posix


def should_exclude(relative_path: Path, name: str, patterns: Iterable[str]) -> bool:
    """Return whether a path or name matches any exclude pattern."""
    relative_posix = relative_path.as_posix()
    return any(
        fnmatch.fnmatchcase(name, pattern)
        or fnmatch.fnmatchcase(relative_posix, pattern)
        or fnmatch.fnmatchcase(relative_posix, f"*/{pattern}")
        for pattern in patterns
    )


def is_binary_file(path: Path) -> bool | None:
    """Return True for binary files, False for likely text, None for read errors."""
    try:
        with path.open("rb") as file:
            chunk = file.read(BINARY_CHECK_BYTES)
    except OSError as exc:
        logger.warning("Could not read file for binary check: %s (%s)", path, exc)
        return None

    return b"\x00" in chunk


def format_section(relative_path: str, content: str, separator: str) -> str:
    """Format one collected file section."""
    normalized_content = content.rstrip("\n")
    return f"{separator}\nFILE: {relative_path}\n{separator}\n\n{normalized_content}\n"


def _same_path(left: Path, right: Path) -> bool:
    try:
        return left.resolve() == right.resolve()
    except OSError:
        return left.absolute() == right.absolute()


def _cleanup_temp_file(temp_path: Path | None) -> None:
    if temp_path is None:
        return
    try:
        temp_path.unlink(missing_ok=True)
    except OSError:
        logger.warning("Failed to remove temporary output file: %s", temp_path)
