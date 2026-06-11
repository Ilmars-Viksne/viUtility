"""Binary detection implementations."""

from __future__ import annotations

from pathlib import Path

from text_file_collector.core.entities import SourceFile
from text_file_collector.core.exceptions import InfrastructureError


class NullByteBinaryDetectionStrategy:
    """Detects binary files by checking for null bytes in an initial chunk."""

    def __init__(self, chunk_size: int = 4096) -> None:
        if chunk_size < 1:
            raise ValueError("chunk_size must be greater than zero.")

        self._chunk_size = chunk_size

    def is_binary(self, source_file: SourceFile) -> bool:
        try:
            with Path(source_file.identifier).open("rb") as file_handle:
                chunk = file_handle.read(self._chunk_size)
        except OSError as exc:
            raise InfrastructureError(f"Could not inspect file: {source_file.relative_path}") from exc

        return b"\x00" in chunk
