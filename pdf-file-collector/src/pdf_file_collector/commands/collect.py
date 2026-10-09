"""Collection / multi-source commands (insert, append, prepend, merge, collect, compose, validate, plan)."""

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from pdf_file_collector.core.exceptions import (
    PageSelectionError,
    SourceSpecificationError,
)
from pdf_file_collector.core.metadata import MetadataManager
from pdf_file_collector.core.models import CollectionPlan, SourceSpecification
from pdf_file_collector.core.output_transaction import OutputTransaction
from pdf_file_collector.core.planner import CollectionPlanner
from pdf_file_collector.core.reader import PdfReaderService
from pdf_file_collector.core.source_spec import SourceSpecificationParser
from pdf_file_collector.core.writer import PdfWriterService
from pdf_file_collector.presentation.console import print_message, print_plan, print_warning
from pdf_file_collector.presentation.json_output import print_json_stdout


def _prepare_multi_source_plan(
    source_specs: Sequence[SourceSpecification],
    output_path: Path | None = None,
    strict: bool = False,
    password: str | None = None,
    password_env: str | None = None,
) -> tuple[CollectionPlan, dict[Path, Any]]:
    readers: dict[Path, Any] = {}

    for spec in source_specs:
        norm_p = spec.path.resolve()
        if norm_p not in readers:
            reader, _ = PdfReaderService.open_pdf(
                path=spec.path,
                password=password,
                password_env=password_env,
                strict=strict,
            )
            readers[norm_p] = reader

    plan = CollectionPlanner.create_plan(
        source_specs=source_specs,
        readers=readers,
        output_path=output_path,
    )
    return plan, readers


def execute_collect_or_compose(
    sources_raw: Sequence[str],
    output_path: Path,
    metadata_from: Path | None = None,
    strict: bool = False,
    password: str | None = None,
    password_env: str | None = None,
    overwrite_output: bool = False,
    dry_run: bool = False,
    json_format: bool = False,
    quiet: bool = False,
    command_name: str = "collect",
) -> None:
    if not sources_raw:
        raise SourceSpecificationError("At least one --source must be specified.")

    specs = [SourceSpecificationParser.parse(s) for s in sources_raw]
    plan, readers = _prepare_multi_source_plan(
        source_specs=specs,
        output_path=output_path,
        strict=strict,
        password=password,
        password_env=password_env,
    )

    plan_lines = [
        f"Output page {p.output_page_number} <- {p.source_path.name} page {p.source_page_number}" for p in plan.pages
    ]

    if dry_run:
        if json_format:
            out_data: dict[str, Any] = {
                "operation": command_name,
                "status": "dry_run",
                "inputs": [str(s.path.resolve()) for s in specs],
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
            print_message(f"[yellow]Dry run completed for {command_name}. No files written.[/yellow]", quiet=quiet)
        return

    writer, warnings = PdfWriterService.assemble_pdf(plan, readers)

    meta_warn = MetadataManager.apply_multi_source_metadata(
        writer=writer,
        metadata_from_path=metadata_from,
        validated_readers=readers,
    )
    if meta_warn:
        warnings.append(meta_warn)

    input_paths = [s.path for s in specs]
    res = OutputTransaction.execute(
        plan=plan,
        writer=writer,
        output_path=output_path,
        input_paths=input_paths,
        overwrite_output=overwrite_output,
        warnings=warnings,
    )

    if json_format:
        out_data = {
            "operation": command_name,
            "status": "success",
            "inputs": [str(p.resolve()) for p in input_paths],
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


def execute_insert(
    base_path: Path,
    donor_path: Path,
    donor_pages_expr: str,
    before_position: int | None = None,
    after_position: str | int | None = None,
    output_path: Path = Path("output.pdf"),
    strict: bool = False,
    password: str | None = None,
    password_env: str | None = None,
    overwrite_output: bool = False,
    dry_run: bool = False,
    json_format: bool = False,
    quiet: bool = False,
) -> None:
    if (before_position is None and after_position is None) or (
        before_position is not None and after_position is not None
    ):
        raise PageSelectionError("Exactly one of --before or --after must be specified.")

    base_reader, _ = PdfReaderService.open_pdf(
        path=base_path, password=password, password_env=password_env, strict=strict
    )
    base_total = len(base_reader.pages)

    if before_position is not None:
        if before_position < 1 or before_position > base_total + 1:
            raise PageSelectionError(
                f"--before position {before_position} is out of bounds for base PDF with {base_total} page(s)."
            )
        insert_after = before_position - 1
    else:
        if str(after_position).lower() == "last":
            insert_after = base_total
        else:
            try:
                val = int(after_position)  # type: ignore
            except ValueError:
                raise PageSelectionError(f"Invalid --after position '{after_position}'.") from None

            if val < 1 or val > base_total:
                raise PageSelectionError(
                    f"--after position {val} is out of bounds for base PDF with {base_total} page(s)."
                )
            insert_after = val

    specs: list[SourceSpecification] = []
    if insert_after > 0:
        specs.append(SourceSpecification(path=base_path, page_expression=f"1-{insert_after}"))
    specs.append(SourceSpecification(path=donor_path, page_expression=donor_pages_expr))
    if insert_after < base_total:
        specs.append(SourceSpecification(path=base_path, page_expression=f"{insert_after + 1}-{base_total}"))

    sources_str = [f"{s.path}::{s.page_expression}" for s in specs]
    execute_collect_or_compose(
        sources_raw=sources_str,
        output_path=output_path,
        strict=strict,
        password=password,
        password_env=password_env,
        overwrite_output=overwrite_output,
        dry_run=dry_run,
        json_format=json_format,
        quiet=quiet,
        command_name="insert",
    )


def execute_append(
    base_path: Path,
    adds_raw: Sequence[str],
    output_path: Path,
    strict: bool = False,
    password: str | None = None,
    password_env: str | None = None,
    overwrite_output: bool = False,
    dry_run: bool = False,
    json_format: bool = False,
    quiet: bool = False,
) -> None:
    if not adds_raw:
        raise SourceSpecificationError("At least one --add specification must be provided.")

    specs = [SourceSpecification(path=base_path, page_expression="all")]
    for add in adds_raw:
        specs.append(SourceSpecificationParser.parse(add))

    sources_str = [f"{s.path}::{s.page_expression}" for s in specs]
    execute_collect_or_compose(
        sources_raw=sources_str,
        output_path=output_path,
        strict=strict,
        password=password,
        password_env=password_env,
        overwrite_output=overwrite_output,
        dry_run=dry_run,
        json_format=json_format,
        quiet=quiet,
        command_name="append",
    )


def execute_prepend(
    base_path: Path,
    adds_raw: Sequence[str],
    output_path: Path,
    strict: bool = False,
    password: str | None = None,
    password_env: str | None = None,
    overwrite_output: bool = False,
    dry_run: bool = False,
    json_format: bool = False,
    quiet: bool = False,
) -> None:
    if not adds_raw:
        raise SourceSpecificationError("At least one --add specification must be provided.")

    specs: list[SourceSpecification] = []
    for add in adds_raw:
        specs.append(SourceSpecificationParser.parse(add))
    specs.append(SourceSpecification(path=base_path, page_expression="all"))

    sources_str = [f"{s.path}::{s.page_expression}" for s in specs]
    execute_collect_or_compose(
        sources_raw=sources_str,
        output_path=output_path,
        strict=strict,
        password=password,
        password_env=password_env,
        overwrite_output=overwrite_output,
        dry_run=dry_run,
        json_format=json_format,
        quiet=quiet,
        command_name="prepend",
    )


def execute_merge(
    positional_paths: Sequence[Path],
    sources_raw: Sequence[str],
    output_path: Path,
    strict: bool = False,
    password: str | None = None,
    password_env: str | None = None,
    overwrite_output: bool = False,
    dry_run: bool = False,
    json_format: bool = False,
    quiet: bool = False,
) -> None:
    if positional_paths and sources_raw:
        raise SourceSpecificationError("Cannot mix positional PDF paths with --source flags in merge command.")

    if not positional_paths and not sources_raw:
        raise SourceSpecificationError("Must provide either positional PDF paths or --source specifications for merge.")

    sources_str: list[str] = []
    if positional_paths:
        for p in positional_paths:
            sources_str.append(f"{p}::all")
    else:
        sources_str = list(sources_raw)

    execute_collect_or_compose(
        sources_raw=sources_str,
        output_path=output_path,
        strict=strict,
        password=password,
        password_env=password_env,
        overwrite_output=overwrite_output,
        dry_run=dry_run,
        json_format=json_format,
        quiet=quiet,
        command_name="merge",
    )


def execute_validate(
    positional_path: Path | None = None,
    pages_expr: str | None = None,
    sources_raw: Sequence[str] = (),
    strict: bool = False,
    password: str | None = None,
    password_env: str | None = None,
    json_format: bool = False,
    quiet: bool = False,
) -> None:
    specs: list[SourceSpecification] = []

    if positional_path is not None:
        expr = pages_expr if pages_expr else "all"
        specs.append(SourceSpecification(path=positional_path, page_expression=expr))

    if sources_raw:
        for s in sources_raw:
            specs.append(SourceSpecificationParser.parse(s))

    if not specs:
        raise SourceSpecificationError("No input PDF files or --source specifications to validate.")

    plan, _ = _prepare_multi_source_plan(
        source_specs=specs,
        strict=strict,
        password=password,
        password_env=password_env,
    )

    if json_format:
        out_data = {
            "operation": "validate",
            "status": "valid",
            "source_count": len(specs),
            "output_page_count": plan.total_output_pages,
            "inputs": [str(s.path.resolve()) for s in specs],
        }
        print_json_stdout(out_data)
    else:
        print_message(
            f"Validation successful. {len(specs)} input(s) validated, "
            f"resolving to {plan.total_output_pages} output page(s).",
            quiet=quiet,
        )


def execute_plan(
    sources_raw: Sequence[str],
    output_path: Path | None = None,
    strict: bool = False,
    password: str | None = None,
    password_env: str | None = None,
    json_format: bool = False,
    quiet: bool = False,
) -> None:
    if not sources_raw:
        raise SourceSpecificationError("At least one --source specification must be provided.")

    specs = [SourceSpecificationParser.parse(s) for s in sources_raw]
    plan, _ = _prepare_multi_source_plan(
        source_specs=specs,
        output_path=output_path,
        strict=strict,
        password=password,
        password_env=password_env,
    )

    plan_lines = [
        f"Output page {p.output_page_number} <- {p.source_path.name} page {p.source_page_number}" for p in plan.pages
    ]

    if json_format:
        out_data = {
            "operation": "plan",
            "status": "success",
            "output_path": str(output_path.resolve()) if output_path else None,
            "sources": [{"path": str(s.path.resolve()), "page_expression": s.page_expression} for s in specs],
            "planned_pages": [
                {
                    "output_page": p.output_page_number,
                    "source": str(p.source_path),
                    "source_page": p.source_page_number,
                }
                for p in plan.pages
            ],
            "total_output_pages": plan.total_output_pages,
        }
        print_json_stdout(out_data)
    else:
        print_plan(
            plan_lines,
            output_path=str(output_path) if output_path else None,
            quiet=quiet,
        )
