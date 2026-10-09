"""Data models for PDF File Collector."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class SourceSpecification:
    """Represents a source specification string parsed into path and page expression."""

    path: Path
    page_expression: str = "all"


@dataclass(frozen=True)
class ResolvedPage:
    """Represents a single mapped page in a collection plan."""

    source_path: Path
    source_page_number: int  # 1-based page number in source
    source_page_index: int  # 0-based page index in source
    output_page_number: int  # 1-based page number in output


@dataclass(frozen=True)
class CollectionPlan:
    """Represents the complete plan of sources and mapped pages."""

    sources: tuple[SourceSpecification, ...]
    pages: tuple[ResolvedPage, ...]
    output_path: Path | None = None

    @property
    def total_output_pages(self) -> int:
        return len(self.pages)


@dataclass(frozen=True)
class OperationResult:
    """Represents the result of an operation execution."""

    output_paths: tuple[Path, ...]
    source_count: int
    output_page_count: int
    warnings: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PdfPageInfo:
    """Represents information about a single PDF page."""

    page_number: int  # 1-based
    width: float
    height: float
    rotation: int


@dataclass(frozen=True)
class PdfDocumentInfo:
    """Represents metadata and properties of a PDF file."""

    path: Path
    file_size_bytes: int
    pdf_version: str | None
    page_count: int
    is_encrypted: bool
    has_metadata: bool
    has_outlines: bool
    has_forms: bool
    pages_info: tuple[PdfPageInfo, ...] = field(default_factory=tuple)
