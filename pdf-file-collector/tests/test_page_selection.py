"""Tests for PageSelectionParser grammar and range operations."""

import pytest

from pdf_file_collector.core.exceptions import PageOutOfRangeError, PageSelectionError
from pdf_file_collector.core.page_selection import PageSelectionParser


def test_single_page() -> None:
    res = PageSelectionParser.parse("1", total_pages=10)
    assert res == [1]


def test_comma_separated() -> None:
    res = PageSelectionParser.parse("1,3,5", total_pages=10)
    assert res == [1, 3, 5]


def test_ascending_range() -> None:
    res = PageSelectionParser.parse("1-5", total_pages=10)
    assert res == [1, 2, 3, 4, 5]


def test_descending_range() -> None:
    res = PageSelectionParser.parse("5-1", total_pages=10)
    assert res == [5, 4, 3, 2, 1]


def test_odd_even_all_last() -> None:
    assert PageSelectionParser.parse("odd", total_pages=5) == [1, 3, 5]
    assert PageSelectionParser.parse("even", total_pages=5) == [2, 4]
    assert PageSelectionParser.parse("all", total_pages=3) == [1, 2, 3]
    assert PageSelectionParser.parse("last", total_pages=5) == [5]
    assert PageSelectionParser.parse("1,last", total_pages=5) == [1, 5]


def test_open_ended_ranges() -> None:
    assert PageSelectionParser.parse("-3", total_pages=5) == [1, 2, 3]
    assert PageSelectionParser.parse("3-", total_pages=5) == [3, 4, 5]
    assert PageSelectionParser.parse("3-last", total_pages=5) == [3, 4, 5]
    assert PageSelectionParser.parse("last-3", total_pages=5) == [5, 4, 3]


def test_unique_deduplication() -> None:
    res = PageSelectionParser.parse("1,3,1,2,3", total_pages=5, unique=True)
    assert res == [1, 3, 2]


def test_page_0_rejection() -> None:
    with pytest.raises(PageOutOfRangeError, match="Page 0 is invalid"):
        PageSelectionParser.parse("0", total_pages=5)


def test_negative_page_rejection() -> None:
    with pytest.raises(PageSelectionError):
        PageSelectionParser.parse("1- -2", total_pages=5)


def test_out_of_range_rejection() -> None:
    with pytest.raises(PageOutOfRangeError, match="out of range"):
        PageSelectionParser.parse("10", total_pages=5)


def test_malformed_tokens() -> None:
    with pytest.raises(PageSelectionError, match="Invalid page token"):
        PageSelectionParser.parse("foo", total_pages=5)

    with pytest.raises(PageSelectionError, match="Empty token"):
        PageSelectionParser.parse("1,,3", total_pages=5)


def test_empty_expression() -> None:
    with pytest.raises(PageSelectionError, match="Empty page selection"):
        PageSelectionParser.parse("   ", total_pages=5)
