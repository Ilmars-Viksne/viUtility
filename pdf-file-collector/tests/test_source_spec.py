"""Tests for SourceSpecificationParser."""

from pathlib import Path

import pytest

from pdf_file_collector.core.exceptions import SourceSpecificationError
from pdf_file_collector.core.source_spec import SourceSpecificationParser


def test_parse_simple_path() -> None:
    spec = SourceSpecificationParser.parse("document.pdf")
    assert spec.path == Path("document.pdf")
    assert spec.page_expression == "all"


def test_parse_path_with_expression() -> None:
    spec = SourceSpecificationParser.parse("cover.pdf::1-3,last")
    assert spec.path == Path("cover.pdf")
    assert spec.page_expression == "1-3,last"


def test_windows_path_handling() -> None:
    spec = SourceSpecificationParser.parse("C:\\Documents\\Report.pdf::1-5")
    assert spec.path == Path("C:\\Documents\\Report.pdf")
    assert spec.page_expression == "1-5"


def test_path_with_spaces() -> None:
    spec = SourceSpecificationParser.parse("./documents/My Report.pdf::2-last")
    assert spec.path == Path("./documents/My Report.pdf")
    assert spec.page_expression == "2-last"


def test_empty_spec_errors() -> None:
    with pytest.raises(SourceSpecificationError, match="Empty source specification"):
        SourceSpecificationParser.parse("")

    with pytest.raises(SourceSpecificationError, match="Empty path"):
        SourceSpecificationParser.parse("::1-5")

    with pytest.raises(SourceSpecificationError, match="Empty page expression"):
        SourceSpecificationParser.parse("doc.pdf::")
