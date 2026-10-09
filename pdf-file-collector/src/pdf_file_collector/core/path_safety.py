"""Path safety and collision detection for PDF File Collector."""

import os
from collections.abc import Sequence
from pathlib import Path

from pdf_file_collector.core.exceptions import (
    InputOutputCollisionError,
    InputPathError,
    OutputExistsError,
)


def normalize_path(path: Path | str) -> Path:
    """Resolve and normalize a filesystem path."""
    p = Path(path)
    try:
        return p.resolve()
    except Exception:
        return p.absolute()


def is_same_file(path1: Path, path2: Path) -> bool:
    """Check if two paths refer to the exact same file.

    Handles non-existent files gracefully by comparing resolved absolute paths.
    Uses os.path.samefile where supported and when both paths exist.
    """
    resolved1 = normalize_path(path1)
    resolved2 = normalize_path(path2)

    if resolved1 == resolved2:
        return True

    if path1.exists() and path2.exists():
        try:
            return os.path.samefile(path1, path2)
        except (OSError, ValueError):
            pass

    return False


def validate_input_path(path: Path) -> Path:
    """Validate that an input path exists and is a regular file."""
    resolved = normalize_path(path)
    if not path.exists():
        from pdf_file_collector.core.exceptions import InputFileNotFoundError

        raise InputFileNotFoundError(f"Input file not found: '{path}'")
    if not path.is_file():
        raise InputPathError(f"Input path is not a file: '{path}'")
    return resolved


def validate_output_safety(
    output_path: Path,
    input_paths: Sequence[Path],
    overwrite_output: bool = False,
) -> Path:
    """Validate output path safety against input collisions and existence rules.

    Rules:
    1. Output path must not refer to the same file as any input path (even with --overwrite-output).
    2. If output path exists and overwrite_output is False, raise OutputExistsError.
    3. If output path exists and is a directory, raise InputPathError.
    """
    resolved_output = normalize_path(output_path)

    for input_path in input_paths:
        if is_same_file(output_path, input_path):
            raise InputOutputCollisionError(
                f"Output path '{output_path}' refers to input file '{input_path}'. "
                "Overwriting input files is strictly prohibited."
            )

    if output_path.exists():
        if output_path.is_dir():
            raise InputPathError(f"Output path '{output_path}' is an existing directory.")
        if not overwrite_output:
            raise OutputExistsError(
                f"Output file '{output_path}' already exists. Use --overwrite-output to allow replacement."
            )

    return resolved_output
