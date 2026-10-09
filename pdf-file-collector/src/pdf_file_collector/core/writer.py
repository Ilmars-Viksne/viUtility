"""PDF Writer service for PDF File Collector."""

from collections.abc import Mapping
from pathlib import Path

import pypdf

from pdf_file_collector.core.models import CollectionPlan


class PdfWriterService:
    """Service for assembling new PDF documents from collection plans without modifying page content."""

    @classmethod
    def assemble_pdf(
        cls,
        plan: CollectionPlan,
        readers: Mapping[Path, pypdf.PdfReader],
    ) -> tuple[pypdf.PdfWriter, list[str]]:
        """Assemble a new pypdf.PdfWriter from plan pages and source readers."""
        writer = pypdf.PdfWriter()
        warnings: list[str] = []

        # Check interactive forms / signatures across readers
        for path, r in readers.items():
            try:
                if r.get_fields():
                    warnings.append(
                        f"Interactive form fields detected in '{path.name}'. Form fields are not preserved."
                    )
            except Exception:
                pass

        for page_mapping in plan.pages:
            norm_path = page_mapping.source_path.resolve()
            reader = readers.get(norm_path)
            if reader is None:
                for p, r in readers.items():
                    if p.resolve() == norm_path:
                        reader = r
                        break

            if reader is None:
                raise KeyError(f"Reader for '{page_mapping.source_path}' not found.")

            source_page = reader.pages[page_mapping.source_page_index]
            writer.add_page(source_page)

        return writer, warnings
