"""Strategy protocols used by the core service."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from text_file_collector.core.entities import SourceFile


class FileDiscoveryStrategy(Protocol):
    """Discovers source files from a collection root."""

    def discover(self, input_directory: str) -> Iterable[SourceFile]:
        """Discover files under the input directory."""


class BinaryDetectionStrategy(Protocol):
    """Determines whether a source file should be treated as binary."""

    def is_binary(self, source_file: SourceFile) -> bool:
        """Return whether the source file is binary."""


class TextReaderStrategy(Protocol):
    """Reads text content from a source file."""

    def read_text(self, source_file: SourceFile) -> str:
        """Read text content."""


class ContentFormatterStrategy(Protocol):
    """Formats one collected file for output."""

    def format_file(self, relative_path: str, content: str) -> str:
        """Format a collected file."""


class OutputWriterStrategy(Protocol):
    """Writes formatted sections to an output destination."""

    def write_sections(self, output_file: str, sections: Iterable[str]) -> int:
        """Write formatted sections and return the number written."""
