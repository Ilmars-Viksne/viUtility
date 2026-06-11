"""Core application service for collecting text files."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path

from text_file_collector.core.entities import CollectionRequest, CollectionResult, SourceFile
from text_file_collector.core.exceptions import CollectionWorkflowError, TextFileCollectorError
from text_file_collector.interfaces.strategies import (
    BinaryDetectionStrategy,
    ContentFormatterStrategy,
    FileDiscoveryStrategy,
    OutputWriterStrategy,
    TextReaderStrategy,
)

logger = logging.getLogger(__name__)


class TextFileCollectionService:
    """Coordinates the text-file collection workflow."""

    def __init__(
        self,
        file_discovery: FileDiscoveryStrategy,
        binary_detector: BinaryDetectionStrategy,
        text_reader: TextReaderStrategy,
        content_formatter: ContentFormatterStrategy,
        output_writer: OutputWriterStrategy,
    ) -> None:
        self._file_discovery = file_discovery
        self._binary_detector = binary_detector
        self._text_reader = text_reader
        self._content_formatter = content_formatter
        self._output_writer = output_writer

    def collect(self, request: CollectionRequest) -> CollectionResult:
        """Collect non-binary text files into the configured output."""
        files_seen = 0
        binary_files_skipped = 0

        def formatted_sections() -> Iterator[str]:
            nonlocal files_seen
            nonlocal binary_files_skipped

            source_files = self._file_discovery.discover(request.input_directory)

            for source_file in source_files:
                files_seen += 1

                if self._is_output_file(source_file, request.output_file):
                    logger.debug("Skipping output file: %s", source_file.relative_path)
                    continue

                if self._binary_detector.is_binary(source_file):
                    binary_files_skipped += 1
                    logger.debug("Skipping binary file: %s", source_file.relative_path)
                    continue

                content = self._text_reader.read_text(source_file)
                yield self._content_formatter.format_file(source_file.relative_path, content)

        try:
            text_files_written = self._output_writer.write_sections(
                request.output_file,
                formatted_sections(),
            )
        except TextFileCollectorError:
            raise
        except Exception as exc:
            raise CollectionWorkflowError("Collection workflow failed.") from exc

        return CollectionResult(
            files_seen=files_seen,
            text_files_written=text_files_written,
            binary_files_skipped=binary_files_skipped,
            output_file=request.output_file,
        )

    @staticmethod
    def _is_output_file(source_file: SourceFile, output_file: str) -> bool:
        try:
            return Path(source_file.identifier).resolve() == Path(output_file).resolve()
        except OSError:
            return source_file.identifier == output_file
