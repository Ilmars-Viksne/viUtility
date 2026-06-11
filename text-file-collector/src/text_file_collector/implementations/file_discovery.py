"""Local file-system discovery implementation."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from text_file_collector.core.entities import SourceFile
from text_file_collector.core.exceptions import InputDirectoryNotFoundError


class LocalFileDiscoveryStrategy:
    """Discovers files recursively from a local directory."""

    def discover(self, input_directory: str) -> Iterable[SourceFile]:
        root = Path(input_directory).expanduser().resolve()

        if not root.is_dir():
            raise InputDirectoryNotFoundError(f"Input directory does not exist: {root}")

        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue

            yield SourceFile(
                identifier=str(path.resolve()),
                relative_path=path.relative_to(root).as_posix(),
            )
