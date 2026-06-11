"""Output writer implementations."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from text_file_collector.core.exceptions import OutputWriteError


class LocalTextOutputWriterStrategy:
    """Writes formatted sections to a local text file."""

    def __init__(self, encoding: str = "utf-8") -> None:
        self._encoding = encoding

    def write_sections(self, output_file: str, sections: Iterable[str]) -> int:
        output_path = Path(output_file).expanduser().resolve()

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            count = 0
            with output_path.open("w", encoding=self._encoding, newline="") as file_handle:
                for section in sections:
                    file_handle.write(section)
                    count += 1

            return count
        except OSError as exc:
            raise OutputWriteError(f"Could not write output file: {output_path}") from exc
