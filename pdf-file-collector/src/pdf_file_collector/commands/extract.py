"""Single-source operations service (extract, remove, reorder, reverse)."""

from pathlib import Path
from typing import Any

from pdf_file_collector.core.metadata import MetadataManager, SingleSourceMetadataPolicy
from pdf_file_collector.core.models import SourceSpecification
from pdf_file_collector.core.output_transaction import OutputTransaction
from pdf_file_collector.core.planner import CollectionPlanner
from pdf_file_collector.core.reader import PdfReaderService
from pdf_file_collector.core.writer import PdfWriterService
from pdf_file_collector.presentation.console import print_message, print_plan, print_warning
from pdf_file_collector.presentation.json_output import print_json_stdout


def _run_single_source_op(
    op_name: str,
    source_path: Path,
    page_expression: str,
    output_path: Path,
    unique: bool = False,
    metadata_policy: SingleSourceMetadataPolicy = SingleSourceMetadataPolicy.KEEP,
    strict: bool = False,
    password: str | None = None,
    password_env: str | None = None,
    overwrite_output: bool = False,
    dry_run: bool = False,
    json_format: bool = False,
    quiet: bool = False,
) -> None:
    norm_source = source_path.resolve()
    reader, _ = PdfReaderService.open_pdf(
        path=source_path,
        password=password,
        password_env=password_env,
        strict=strict,
    )

    readers = {norm_source: reader}
    source_spec = SourceSpecification(path=source_path, page_expression=page_expression)

    plan = CollectionPlanner.create_plan(
        source_specs=[source_spec],
        readers=readers,
        unique=unique,
        output_path=output_path,
    )

    plan_lines = [
        f"Output page {p.output_page_number} <- {p.source_path.name} page {p.source_page_number}" for p in plan.pages
    ]

    if dry_run:
        if json_format:
            out_data: dict[str, Any] = {
                "operation": op_name,
                "status": "dry_run",
                "inputs": [str(norm_source)],
                "output": str(output_path.resolve()),
                "planned_pages": [
                    {
                        "output_page": p.output_page_number,
                        "source": str(p.source_path),
                        "source_page": p.source_page_number,
                    }
                    for p in plan.pages
                ],
                "output_page_count": plan.total_output_pages,
                "warnings": [],
            }
            print_json_stdout(out_data)
        else:
            print_plan(plan_lines, output_path=str(output_path))
            print_message(f"[yellow]Dry run completed for {op_name}. No files written.[/yellow]", quiet=quiet)
        return

    writer, warnings = PdfWriterService.assemble_pdf(plan, readers)
    MetadataManager.apply_single_source_metadata(reader, writer, metadata_policy)

    res = OutputTransaction.execute(
        plan=plan,
        writer=writer,
        output_path=output_path,
        input_paths=[source_path],
        overwrite_output=overwrite_output,
        warnings=warnings,
    )

    if json_format:
        out_data = {
            "operation": op_name,
            "status": "success",
            "inputs": [str(norm_source)],
            "output": str(res.output_paths[0]),
            "output_page_count": res.output_page_count,
            "warnings": list(res.warnings),
        }
        print_json_stdout(out_data)
    else:
        for w in res.warnings:
            print_warning(w, quiet=quiet)
        print_message(
            f"Successfully created '{res.output_paths[0]}' with {res.output_page_count} page(s).",
            quiet=quiet,
        )


def execute_extract(
    source_path: Path,
    pages_expr: str,
    output_path: Path,
    unique: bool = False,
    metadata_policy: SingleSourceMetadataPolicy = SingleSourceMetadataPolicy.KEEP,
    strict: bool = False,
    password: str | None = None,
    password_env: str | None = None,
    overwrite_output: bool = False,
    dry_run: bool = False,
    json_format: bool = False,
    quiet: bool = False,
) -> None:
    _run_single_source_op(
        op_name="extract",
        source_path=source_path,
        page_expression=pages_expr,
        output_path=output_path,
        unique=unique,
        metadata_policy=metadata_policy,
        strict=strict,
        password=password,
        password_env=password_env,
        overwrite_output=overwrite_output,
        dry_run=dry_run,
        json_format=json_format,
        quiet=quiet,
    )


def execute_remove(
    source_path: Path,
    pages_expr: str,
    output_path: Path,
    metadata_policy: SingleSourceMetadataPolicy = SingleSourceMetadataPolicy.KEEP,
    strict: bool = False,
    password: str | None = None,
    password_env: str | None = None,
    overwrite_output: bool = False,
    dry_run: bool = False,
    json_format: bool = False,
    quiet: bool = False,
) -> None:
    # First inspect document total pages
    reader, _ = PdfReaderService.open_pdf(path=source_path, password=password, password_env=password_env, strict=strict)
    total_pages = len(reader.pages)

    from pdf_file_collector.core.exceptions import PageSelectionError
    from pdf_file_collector.core.page_selection import PageSelectionParser

    remove_set = set(PageSelectionParser.parse(pages_expr, total_pages, unique=True, source_path=source_path))

    retained_pages = [p for p in range(1, total_pages + 1) if p not in remove_set]

    if not retained_pages:
        raise PageSelectionError("Cannot remove all pages from PDF document.")

    retained_expr = ",".join(map(str, retained_pages))

    _run_single_source_op(
        op_name="remove",
        source_path=source_path,
        page_expression=retained_expr,
        output_path=output_path,
        unique=False,
        metadata_policy=metadata_policy,
        strict=strict,
        password=password,
        password_env=password_env,
        overwrite_output=overwrite_output,
        dry_run=dry_run,
        json_format=json_format,
        quiet=quiet,
    )


def execute_reorder(
    source_path: Path,
    pages_expr: str,
    output_path: Path,
    unique: bool = False,
    metadata_policy: SingleSourceMetadataPolicy = SingleSourceMetadataPolicy.KEEP,
    strict: bool = False,
    password: str | None = None,
    password_env: str | None = None,
    overwrite_output: bool = False,
    dry_run: bool = False,
    json_format: bool = False,
    quiet: bool = False,
) -> None:
    _run_single_source_op(
        op_name="reorder",
        source_path=source_path,
        page_expression=pages_expr,
        output_path=output_path,
        unique=unique,
        metadata_policy=metadata_policy,
        strict=strict,
        password=password,
        password_env=password_env,
        overwrite_output=overwrite_output,
        dry_run=dry_run,
        json_format=json_format,
        quiet=quiet,
    )


def execute_reverse(
    source_path: Path,
    output_path: Path,
    pages_expr: str | None = None,
    metadata_policy: SingleSourceMetadataPolicy = SingleSourceMetadataPolicy.KEEP,
    strict: bool = False,
    password: str | None = None,
    password_env: str | None = None,
    overwrite_output: bool = False,
    dry_run: bool = False,
    json_format: bool = False,
    quiet: bool = False,
) -> None:
    reader, _ = PdfReaderService.open_pdf(path=source_path, password=password, password_env=password_env, strict=strict)
    total_pages = len(reader.pages)

    if pages_expr is not None and pages_expr.strip():
        from pdf_file_collector.core.page_selection import PageSelectionParser

        sel_pages = PageSelectionParser.parse(pages_expr, total_pages, unique=False, source_path=source_path)
        reversed_pages = list(reversed(sel_pages))
    else:
        reversed_pages = list(range(total_pages, 0, -1))

    rev_expr = ",".join(map(str, reversed_pages))

    _run_single_source_op(
        op_name="reverse",
        source_path=source_path,
        page_expression=rev_expr,
        output_path=output_path,
        unique=False,
        metadata_policy=metadata_policy,
        strict=strict,
        password=password,
        password_env=password_env,
        overwrite_output=overwrite_output,
        dry_run=dry_run,
        json_format=json_format,
        quiet=quiet,
    )
