"""PDF collection planner for PDF File Collector."""

from collections.abc import Sequence
from pathlib import Path

import pypdf

from pdf_file_collector.core.exceptions import EmptyOutputError
from pdf_file_collector.core.models import CollectionPlan, ResolvedPage, SourceSpecification
from pdf_file_collector.core.page_selection import PageSelectionParser


class CollectionPlanner:
    """Creates exact CollectionPlans from source specifications and PDF readers."""

    @classmethod
    def create_plan(
        cls,
        source_specs: Sequence[SourceSpecification],
        readers: dict[Path, pypdf.PdfReader],
        unique: bool = False,
        output_path: Path | None = None,
    ) -> CollectionPlan:
        """Create a CollectionPlan mapping input pages to output pages.

        Args:
            source_specs: Sequence of SourceSpecifications.
            readers: Mapping from normalized Path to authenticated pypdf.PdfReader.
            unique: If True, duplicate output pages across sources are ignored (or within source).
            output_path: Optional output path.

        Returns:
            CollectionPlan
        """
        resolved_pages: list[ResolvedPage] = []
        out_page_counter = 1

        for spec in source_specs:
            norm_path = spec.path.resolve()
            reader = readers.get(norm_path)
            if reader is None:
                # Try finding by path equivalence
                for p, r in readers.items():
                    if p.resolve() == norm_path:
                        reader = r
                        break

            if reader is None:
                raise KeyError(f"Reader for '{spec.path}' was not provided.")

            total_pages = len(reader.pages)
            selected_1based = PageSelectionParser.parse(
                expression=spec.page_expression,
                total_pages=total_pages,
                unique=unique,
                source_path=spec.path,
            )

            for source_num in selected_1based:
                res = ResolvedPage(
                    source_path=spec.path,
                    source_page_number=source_num,
                    source_page_index=source_num - 1,
                    output_page_number=out_page_counter,
                )
                resolved_pages.append(res)
                out_page_counter += 1

        if not resolved_pages:
            raise EmptyOutputError("Collection plan resolved to zero output pages.")

        return CollectionPlan(
            sources=tuple(source_specs),
            pages=tuple(resolved_pages),
            output_path=output_path,
        )
