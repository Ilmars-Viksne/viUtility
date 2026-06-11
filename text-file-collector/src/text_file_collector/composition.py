"""Composition root for dependency injection."""

from __future__ import annotations

from pathlib import Path

from text_file_collector.config import Settings
from text_file_collector.core.service import TextFileCollectionService
from text_file_collector.implementations.binary_detection import NullByteBinaryDetectionStrategy
from text_file_collector.implementations.file_discovery import LocalFileDiscoveryStrategy
from text_file_collector.implementations.formatting import PlainTextContentFormatterStrategy
from text_file_collector.implementations.text_reading import Utf8TextReaderStrategy
from text_file_collector.implementations.writing import LocalTextOutputWriterStrategy


def build_collection_service(settings: Settings) -> TextFileCollectionService:
    """Build a ready-to-use collection service."""
    return TextFileCollectionService(
        file_discovery=LocalFileDiscoveryStrategy(),
        binary_detector=NullByteBinaryDetectionStrategy(
            chunk_size=settings.binary_detection_chunk_size,
        ),
        text_reader=Utf8TextReaderStrategy(
            encoding=settings.default_encoding,
        ),
        content_formatter=PlainTextContentFormatterStrategy(
            separator_length=settings.output_separator_length,
        ),
        output_writer=LocalTextOutputWriterStrategy(
            encoding=settings.default_encoding,
        ),
    )


def normalize_output_path(output_file: Path) -> str:
    """Normalize output path for service comparison and writing."""
    return str(output_file.expanduser().resolve())


def normalize_input_path(input_directory: Path) -> str:
    """Normalize input path for service usage."""
    return str(input_directory.expanduser().resolve())
