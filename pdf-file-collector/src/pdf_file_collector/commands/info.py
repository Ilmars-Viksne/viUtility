"""Info command implementation."""

from pathlib import Path
from typing import Any

from pdf_file_collector.core.reader import PdfReaderService
from pdf_file_collector.presentation.console import print_message
from pdf_file_collector.presentation.json_output import print_json_stdout


def execute_info(
    pdf_path: Path,
    pages_expr: str = "all",
    json_format: bool = False,
    strict: bool = False,
    password: str | None = None,
    password_env: str | None = None,
    quiet: bool = False,
) -> None:
    """Inspect PDF properties and output report."""
    doc_info = PdfReaderService.get_document_info(
        path=pdf_path,
        pages_expr=pages_expr,
        password=password,
        password_env=password_env,
        strict=strict,
    )

    if json_format:
        pages_data = [
            {
                "page_number": p.page_number,
                "width": p.width,
                "height": p.height,
                "rotation": p.rotation,
            }
            for p in doc_info.pages_info
        ]
        out_data: dict[str, Any] = {
            "operation": "info",
            "status": "success",
            "path": str(doc_info.path.resolve()),
            "file_size_bytes": doc_info.file_size_bytes,
            "pdf_version": doc_info.pdf_version,
            "total_pages": doc_info.page_count,
            "is_encrypted": doc_info.is_encrypted,
            "has_metadata": doc_info.has_metadata,
            "has_outlines": doc_info.has_outlines,
            "has_forms": doc_info.has_forms,
            "pages": pages_data,
        }
        print_json_stdout(out_data)
        return

    if not quiet:
        lines = [
            f"[bold]PDF Information:[/bold] {doc_info.path.resolve()}",
            f"  File size: {doc_info.file_size_bytes} bytes",
            f"  PDF version: {doc_info.pdf_version or 'Unknown'}",
            f"  Total pages: {doc_info.page_count}",
            f"  Encrypted: {doc_info.is_encrypted}",
            f"  Has metadata: {doc_info.has_metadata}",
            f"  Has outlines/bookmarks: {doc_info.has_outlines}",
            f"  Has forms: {doc_info.has_forms}",
            "\n[bold]Selected Pages Info:[/bold]",
        ]
        for p in doc_info.pages_info:
            lines.append(f"  Page {p.page_number}: {p.width:.1f} x {p.height:.1f} pt (Rotation: {p.rotation}°)")
        print_message("\n".join(lines))
