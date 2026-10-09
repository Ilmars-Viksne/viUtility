"""Tests for CollectionPlanner, path safety, and output transactions."""

from pathlib import Path

import pypdf
import pytest

from pdf_file_collector.core.exceptions import (
    InputOutputCollisionError,
    OutputExistsError,
)
from pdf_file_collector.core.models import SourceSpecification
from pdf_file_collector.core.output_transaction import OutputTransaction
from pdf_file_collector.core.path_safety import validate_output_safety
from pdf_file_collector.core.planner import CollectionPlanner
from pdf_file_collector.core.reader import PdfReaderService
from pdf_file_collector.core.writer import PdfWriterService


def test_planner_resolves_pages(sample_pdf_5p: Path) -> None:
    reader, _ = PdfReaderService.open_pdf(sample_pdf_5p)
    norm_path = sample_pdf_5p.resolve()
    readers = {norm_path: reader}

    spec = SourceSpecification(path=sample_pdf_5p, page_expression="1,3,5")
    plan = CollectionPlanner.create_plan([spec], readers)

    assert len(plan.pages) == 3
    assert [p.source_page_number for p in plan.pages] == [1, 3, 5]
    assert [p.output_page_number for p in plan.pages] == [1, 2, 3]


def test_output_safety_refuses_input_collision(sample_pdf_5p: Path) -> None:
    with pytest.raises(InputOutputCollisionError, match="refers to input file"):
        validate_output_safety(
            output_path=sample_pdf_5p,
            input_paths=[sample_pdf_5p],
            overwrite_output=True,
        )


def test_output_safety_refuses_existing_output_without_overwrite(sample_pdf_5p: Path, tmp_path: Path) -> None:
    out_file = tmp_path / "existing.pdf"
    out_file.touch()

    with pytest.raises(OutputExistsError, match="already exists"):
        validate_output_safety(
            output_path=out_file,
            input_paths=[sample_pdf_5p],
            overwrite_output=False,
        )


def test_single_output_transaction(sample_pdf_5p: Path, tmp_path: Path) -> None:
    reader, _ = PdfReaderService.open_pdf(sample_pdf_5p)
    readers = {sample_pdf_5p.resolve(): reader}

    spec = SourceSpecification(path=sample_pdf_5p, page_expression="1-2")
    plan = CollectionPlanner.create_plan([spec], readers)
    writer, warnings = PdfWriterService.assemble_pdf(plan, readers)

    out_file = tmp_path / "output.pdf"
    res = OutputTransaction.execute(
        plan=plan,
        writer=writer,
        output_path=out_file,
        input_paths=[sample_pdf_5p],
    )

    assert out_file.exists()
    assert res.output_page_count == 2

    # Verify generated output can be reopened and has 2 pages
    out_reader = pypdf.PdfReader(str(out_file))
    assert len(out_reader.pages) == 2
