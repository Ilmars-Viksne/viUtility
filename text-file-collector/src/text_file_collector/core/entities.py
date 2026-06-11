"""Core entities for the text file collection workflow."""

from __future__ import annotations

from dataclasses import dataclass

from text_file_collector.core.exceptions import InvalidCollectionRequestError


@dataclass(frozen=True)
class CollectionRequest:
    """Represents a request to collect text files."""

    input_directory: str
    output_file: str

    def __post_init__(self) -> None:
        if not self.input_directory.strip():
            raise InvalidCollectionRequestError("Input directory must not be empty.")

        if not self.output_file.strip():
            raise InvalidCollectionRequestError("Output file must not be empty.")


@dataclass(frozen=True)
class SourceFile:
    """Represents a discovered source file."""

    identifier: str
    relative_path: str

    def __post_init__(self) -> None:
        if not self.identifier.strip():
            raise InvalidCollectionRequestError("Source file identifier must not be empty.")

        if not self.relative_path.strip():
            raise InvalidCollectionRequestError("Source file relative path must not be empty.")


@dataclass(frozen=True)
class CollectedFile:
    """Represents one text file selected for output."""

    relative_path: str
    content: str


@dataclass(frozen=True)
class CollectionResult:
    """Represents the outcome of a collection run."""

    files_seen: int
    text_files_written: int
    binary_files_skipped: int
    output_file: str
