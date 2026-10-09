"""Metadata policy handler for PDF File Collector."""

from enum import StrEnum
from pathlib import Path

import pypdf

from pdf_file_collector.core.exceptions import InputFileNotFoundError


class SingleSourceMetadataPolicy(StrEnum):
    KEEP = "keep"
    DROP = "drop"


class MetadataManager:
    """Manages reading and transferring metadata between PDF documents."""

    @classmethod
    def apply_single_source_metadata(
        cls,
        reader: pypdf.PdfReader,
        writer: pypdf.PdfWriter,
        policy: SingleSourceMetadataPolicy,
    ) -> None:
        """Apply metadata policy for single-source operations."""
        if policy == SingleSourceMetadataPolicy.KEEP:
            if reader.metadata is not None:
                writer.add_metadata(reader.metadata)

    @classmethod
    def apply_multi_source_metadata(
        cls,
        writer: pypdf.PdfWriter,
        metadata_from_path: Path | None,
        validated_readers: dict[Path, pypdf.PdfReader],
    ) -> str | None:
        """Apply metadata from specified source path in multi-source operations.

        If metadata_from_path is None, defaults to drop metadata.
        Returns a warning string if metadata was requested but not found/empty.
        """
        if metadata_from_path is None:
            return None

        # Resolve path matching
        resolved_target = metadata_from_path.resolve()
        reader_to_use: pypdf.PdfReader | None = None

        for path, r in validated_readers.items():
            if path.resolve() == resolved_target:
                reader_to_use = r
                break

        if reader_to_use is None:
            raise InputFileNotFoundError(
                f"--metadata-from path '{metadata_from_path}' must be one of the validated source inputs."
            )

        if reader_to_use.metadata is not None:
            writer.add_metadata(reader_to_use.metadata)
            return None
        else:
            return f"Metadata source '{metadata_from_path}' has no metadata."
