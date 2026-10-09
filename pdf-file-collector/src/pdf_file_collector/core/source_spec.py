"""Source specification parser for PDF File Collector."""

from pathlib import Path

from pdf_file_collector.core.exceptions import SourceSpecificationError
from pdf_file_collector.core.models import SourceSpecification


class SourceSpecificationParser:
    """Parses source specification strings in the format `PATH::PAGE_EXPRESSION`.

    Examples:
      - "cover.pdf::1"
      - "report.pdf::1-12"
      - "appendix.pdf::3,1,2"
      - "C:\\Documents\\Report.pdf::1-5"
      - "./documents/My Report.pdf::2-last"
      - "document.pdf"  (defaults expression to "all")
    """

    @classmethod
    def parse(cls, spec_str: str, default_expression: str = "all") -> SourceSpecification:
        """Parse source specification string into SourceSpecification model.

        Splits on the last occurrence of `::` to handle paths safely.
        """
        s = spec_str.strip()
        if not s:
            raise SourceSpecificationError("Empty source specification string.")

        if "::" in s:
            parts = s.rsplit("::", 1)
            path_part = parts[0].strip()
            expr_part = parts[1].strip()

            if not path_part:
                raise SourceSpecificationError(f"Empty path in source specification '{spec_str}'.")
            if not expr_part:
                raise SourceSpecificationError(
                    f"Empty page expression after '::' in source specification '{spec_str}'."
                )

            return SourceSpecification(path=Path(path_part), page_expression=expr_part)
        else:
            return SourceSpecification(path=Path(s), page_expression=default_expression)
