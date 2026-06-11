"""Output formatting implementations."""

from __future__ import annotations


class PlainTextContentFormatterStrategy:
    """Formats collected files as plain text sections."""

    def __init__(self, separator_length: int = 80) -> None:
        if separator_length < 1:
            raise ValueError("separator_length must be greater than zero.")

        self._separator = "=" * separator_length

    def format_file(self, relative_path: str, content: str) -> str:
        return f"{self._separator}\nFILE: {relative_path}\n{self._separator}\n\n{content}\n"
