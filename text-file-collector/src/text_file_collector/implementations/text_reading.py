"""Text reading implementations."""

from __future__ import annotations

from pathlib import Path

from text_file_collector.core.entities import SourceFile
from text_file_collector.core.exceptions import InfrastructureError


class Utf8TextReaderStrategy:
    """Reads local files as text with a configurable encoding."""

    def __init__(self, encoding: str = "utf-8") -> None:
        self._encoding = encoding

    def read_text(self, source_file: SourceFile) -> str:
        try:
            return Path(source_file.identifier).read_text(encoding=self._encoding)
        except UnicodeDecodeError as exc:
            raise InfrastructureError(
                f"Could not decode text file {source_file.relative_path!r} as {self._encoding}."
            ) from exc
        except OSError as exc:
            raise InfrastructureError(f"Could not read file: {source_file.relative_path}") from exc
