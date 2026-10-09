"""Page selection expression parser for PDF File Collector."""

from pathlib import Path

from pdf_file_collector.core.exceptions import PageOutOfRangeError, PageSelectionError


class PageSelectionParser:
    """Parses page selection expressions into zero-based indices and one-based numbers.

    Supports expressions such as:
      - 1
      - 1,3,5
      - 1-5
      - 5-1 (descending)
      - odd, even, all, last
      - 1,last
      - 3-last, last-3
      - -5 (1 to 5)
      - 8- (8 to total)

    Options:
      - unique: bool (removes duplicates while preserving order)
    """

    @classmethod
    def parse(
        cls,
        expression: str,
        total_pages: int,
        unique: bool = False,
        source_path: Path | str | None = None,
    ) -> list[int]:
        """Parse expression and return 1-based page numbers in requested sequence."""
        path_str = f" in '{source_path}'" if source_path else ""

        if total_pages < 1:
            raise PageSelectionError(f"Document{path_str} has no pages.")

        expr = expression.strip()
        if not expr:
            raise PageSelectionError(f"Empty page selection expression{path_str}.")

        tokens = [t.strip() for t in expr.split(",")]
        result_pages: list[int] = []

        for token in tokens:
            if not token:
                raise PageSelectionError(f"Empty token in page selection '{expression}'{path_str}.")

            parsed_token_pages = cls._parse_single_token(token, total_pages, expression, path_str)
            result_pages.extend(parsed_token_pages)

        if not result_pages:
            raise PageSelectionError(f"Page selection '{expression}'{path_str} resolved to zero pages.")

        if unique:
            seen: set[int] = set()
            deduped: list[int] = []
            for p in result_pages:
                if p not in seen:
                    seen.add(p)
                    deduped.append(p)
            result_pages = deduped

        return result_pages

    @classmethod
    def _parse_single_token(
        cls,
        token: str,
        total_pages: int,
        full_expression: str,
        path_str: str,
    ) -> list[int]:
        low_token = token.lower()

        if low_token == "all":
            return list(range(1, total_pages + 1))
        if low_token == "odd":
            return [p for p in range(1, total_pages + 1) if p % 2 != 0]
        if low_token == "even":
            return [p for p in range(1, total_pages + 1) if p % 2 == 0]
        if low_token == "last":
            return [total_pages]

        # Check for range with '-'
        if "-" in token:
            parts = token.split("-")
            if len(parts) != 2:
                raise PageSelectionError(
                    f"Invalid range syntax token '{token}' in expression '{full_expression}'{path_str}."
                )

            start_str, end_str = parts[0].strip(), parts[1].strip()

            # Case: -5 -> 1-5
            if start_str == "":
                start = 1
            else:
                start = cls._parse_endpoint(start_str, total_pages, full_expression, token, path_str)

            # Case: 8- -> 8-total_pages
            if end_str == "":
                end = total_pages
            else:
                end = cls._parse_endpoint(end_str, total_pages, full_expression, token, path_str)

            if start <= end:
                return list(range(start, end + 1))
            else:
                # Descending range: e.g. 5-1 -> 5, 4, 3, 2, 1
                return list(range(start, end - 1, -1))

        # Single page number or endpoint
        page_num = cls._parse_endpoint(token, total_pages, full_expression, token, path_str)
        return [page_num]

    @classmethod
    def _parse_endpoint(
        cls,
        endpoint_str: str,
        total_pages: int,
        full_expression: str,
        token: str,
        path_str: str,
    ) -> int:
        low = endpoint_str.lower()
        if low == "last":
            return total_pages

        try:
            val = int(endpoint_str)
        except ValueError:
            raise PageSelectionError(
                f"Invalid page token '{endpoint_str}' in expression '{full_expression}'{path_str}."
            ) from None

        if val == 0:
            raise PageOutOfRangeError(f"Page 0 is invalid (pages are 1-based) in token '{endpoint_str}'{path_str}.")
        if val < 0:
            raise PageOutOfRangeError(f"Negative page number {val} is invalid in token '{endpoint_str}'{path_str}.")
        if val > total_pages:
            raise PageOutOfRangeError(f"Page {val} is out of range (document has {total_pages} page(s)){path_str}.")

        return val
