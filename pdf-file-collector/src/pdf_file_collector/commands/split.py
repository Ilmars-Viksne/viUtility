"""Split command implementation for PDF File Collector."""

from pathlib import Path
from typing import Any

import pypdf

from pdf_file_collector.core.exceptions import (
    InputPathError,
    PageSelectionError,
)
from pdf_file_collector.core.models import CollectionPlan, SourceSpecification
from pdf_file_collector.core.output_transaction import MultiOutputTransaction
from pdf_file_collector.core.planner import CollectionPlanner
from pdf_file_collector.core.reader import PdfReaderService
from pdf_file_collector.core.writer import PdfWriterService
from pdf_file_collector.presentation.console import print_message, print_warning
from pdf_file_collector.presentation.json_output import print_json_stdout


def execute_split(
    source_path: Path,
    output_dir: Path,
    every: int | None = None,
    ranges_raw: str | None = None,
    at_raw: str | None = None,
    strict: bool = False,
    password: str | None = None,
    password_env: str | None = None,
    overwrite_output: bool = False,
    dry_run: bool = False,
    json_format: bool = False,
    quiet: bool = False,
) -> None:
    # Validate exactly one split mode is provided
    modes_set = [m for m in (every, ranges_raw, at_raw) if m is not None]
    if len(modes_set) != 1:
        raise PageSelectionError("Exactly one split mode (--every, --ranges, or --at) must be specified.")

    # Check if output_dir exists and is not a directory
    if output_dir.exists() and not output_dir.is_dir():
        raise InputPathError(f"Split output path '{output_dir}' exists and is not a directory.")

    reader, _ = PdfReaderService.open_pdf(path=source_path, password=password, password_env=password_env, strict=strict)
    norm_source = source_path.resolve()
    readers = {norm_source: reader}
    total_pages = len(reader.pages)

    chunk_exprs: list[str] = []

    if every is not None:
        if every <= 0:
            raise PageSelectionError(f"--every must be greater than 0, got {every}.")
        for start in range(1, total_pages + 1, every):
            end = min(start + every - 1, total_pages)
            if start == end:
                chunk_exprs.append(str(start))
            else:
                chunk_exprs.append(f"{start}-{end}")

    elif ranges_raw is not None:
        raw_parts = [r.strip() for r in ranges_raw.split(";") if r.strip()]
        if not raw_parts:
            raise PageSelectionError("--ranges string cannot be empty.")
        chunk_exprs = raw_parts

    elif at_raw is not None:
        try:
            at_points = sorted(set(int(p.strip()) for p in at_raw.split(",") if p.strip()))
        except ValueError:
            raise PageSelectionError(f"Invalid page numbers in --at '{at_raw}'.") from None

        for pt in at_points:
            if pt <= 1 or pt > total_pages:
                raise PageSelectionError(
                    f"Split point {pt} in --at is out of range for PDF with {total_pages} page(s)."
                )

        # Build ranges around split points
        current_start = 1
        for pt in at_points:
            end = pt - 1
            if current_start == end:
                chunk_exprs.append(str(current_start))
            else:
                chunk_exprs.append(f"{current_start}-{end}")
            current_start = pt
        # Remaining range
        if current_start == total_pages:
            chunk_exprs.append(str(current_start))
        else:
            chunk_exprs.append(f"{current_start}-{total_pages}")

    # Build collection plans and determine destination file names
    stem = source_path.stem
    plans_and_writers: list[tuple[CollectionPlan, pypdf.PdfWriter, Path]] = []

    for _idx, expr in enumerate(chunk_exprs, start=1):
        spec = SourceSpecification(path=source_path, page_expression=expr)
        plan = CollectionPlanner.create_plan([spec], readers)

        start_p = plan.pages[0].source_page_number
        end_p = plan.pages[-1].source_page_number

        if len(plan.pages) == 1:
            filename = f"{stem}_page_{start_p:04d}.pdf"
        else:
            filename = f"{stem}_pages_{start_p:04d}-{end_p:04d}.pdf"

        # Check for potential filename collisions in same split batch by appending chunk index if needed
        dest_file = output_dir / filename

        writer, warnings = PdfWriterService.assemble_pdf(plan, readers)
        plans_and_writers.append((plan, writer, dest_file))

    dest_paths = [p for _, _, p in plans_and_writers]

    if dry_run:
        if json_format:
            out_data: dict[str, Any] = {
                "operation": "split",
                "status": "dry_run",
                "inputs": [str(norm_source)],
                "output_dir": str(output_dir.resolve()),
                "outputs": [str(p.resolve()) for p in dest_paths],
                "total_chunks": len(dest_paths),
                "warnings": [],
            }
            print_json_stdout(out_data)
        else:
            print_message(f"[bold]Split Plan ({len(dest_paths)} files):[/bold]")
            for _, _, dest_file in plans_and_writers:
                print_message(f"  Destination: {dest_file}")
            print_message("[yellow]Dry run completed for split. No files created.[/yellow]", quiet=quiet)
        return

    # Execute multi-output transaction (handles directory creation and atomic staging/validation)
    res = MultiOutputTransaction.execute(
        plans_and_writers=plans_and_writers,
        input_paths=[source_path],
        overwrite_output=overwrite_output,
    )

    if json_format:
        out_data = {
            "operation": "split",
            "status": "success",
            "inputs": [str(norm_source)],
            "output_dir": str(output_dir.resolve()),
            "outputs": [str(p) for p in res.output_paths],
            "total_chunks": len(res.output_paths),
            "output_page_count": res.output_page_count,
            "warnings": list(res.warnings),
        }
        print_json_stdout(out_data)
    else:
        for w in res.warnings:
            print_warning(w, quiet=quiet)
        print_message(
            f"Successfully split into {len(res.output_paths)} files in '{output_dir}'.",
            quiet=quiet,
        )
