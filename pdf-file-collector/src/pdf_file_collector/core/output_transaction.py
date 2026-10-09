"""Output transaction services for atomic PDF generation and verification."""

import os
import tempfile
from collections.abc import Sequence
from pathlib import Path

import pypdf

from pdf_file_collector.core.exceptions import (
    AtomicWriteError,
    DuplicateOutputError,
    OutputValidationError,
)
from pdf_file_collector.core.models import CollectionPlan, OperationResult
from pdf_file_collector.core.path_safety import validate_output_safety


class OutputTransaction:
    """Manages single-output atomic creation, staging, verification, and commit."""

    @classmethod
    def execute(
        cls,
        plan: CollectionPlan,
        writer: pypdf.PdfWriter,
        output_path: Path,
        input_paths: Sequence[Path],
        overwrite_output: bool = False,
        warnings: Sequence[str] = (),
    ) -> OperationResult:
        """Execute output transaction for a single output file."""
        norm_output = validate_output_safety(
            output_path=output_path,
            input_paths=input_paths,
            overwrite_output=overwrite_output,
        )

        dest_dir = norm_output.parent
        if not dest_dir.exists():
            try:
                dest_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise AtomicWriteError(f"Failed to create destination directory '{dest_dir}': {e}") from e

        # Create staging file in destination directory
        staging_fd, staging_path_str = tempfile.mkstemp(
            dir=dest_dir,
            prefix=".tmp_pdf_collector_",
            suffix=".staged",
        )
        staging_path = Path(staging_path_str)

        try:
            # Step 15: Write staged PDF
            with os.fdopen(staging_fd, "wb") as f:
                writer.write(f)
                # Step 16: Flush buffered data
                f.flush()
                # Step 17: os.fsync
                try:
                    os.fsync(f.fileno())
                except (OSError, AttributeError):
                    pass

            # Step 19: Reopen staged PDF with PdfReader and validate
            cls.validate_staged_pdf(staging_path, plan.total_output_pages)

            # Step 22: Commit staged output with atomic rename / replace
            if norm_output.exists() and overwrite_output:
                staging_path.replace(norm_output)
            else:
                try:
                    staging_path.rename(norm_output)
                except OSError:
                    staging_path.replace(norm_output)

        except Exception as e:
            # Step 23: Clean up staging file on failure
            if staging_path.exists():
                try:
                    staging_path.unlink()
                except OSError:
                    pass
            if isinstance(e, (AtomicWriteError, OutputValidationError)):
                raise
            raise AtomicWriteError(f"Failed to write output file '{output_path}': {e}") from e

        return OperationResult(
            output_paths=(norm_output,),
            source_count=len(set(p.source_path.resolve() for p in plan.pages)),
            output_page_count=plan.total_output_pages,
            warnings=tuple(warnings),
        )

    @classmethod
    def validate_staged_pdf(cls, staging_path: Path, expected_page_count: int) -> None:
        """Verify that staged PDF can be parsed and page count matches plan."""
        try:
            reader = pypdf.PdfReader(str(staging_path))
            actual_count = len(reader.pages)
        except Exception as e:
            raise OutputValidationError(f"Staged output PDF failed parsing verification: {e}") from e

        if actual_count != expected_page_count:
            raise OutputValidationError(
                f"Staged output PDF page count mismatch: expected {expected_page_count}, got {actual_count}."
            )


class MultiOutputTransaction:
    """Manages multi-output atomic creation (e.g. for split) with rollbacks on failure."""

    @classmethod
    def execute(
        cls,
        plans_and_writers: Sequence[tuple[CollectionPlan, pypdf.PdfWriter, Path]],
        input_paths: Sequence[Path],
        overwrite_output: bool = False,
        warnings: Sequence[str] = (),
    ) -> OperationResult:
        """Execute transaction for multiple output files."""
        # Step 1: Validate all target output paths and check collisions
        resolved_targets: list[Path] = []
        for _, _, out_path in plans_and_writers:
            norm_out = validate_output_safety(
                output_path=out_path,
                input_paths=input_paths,
                overwrite_output=overwrite_output,
            )
            resolved_targets.append(norm_out)

        # Detect duplicate destination paths among outputs
        if len(set(resolved_targets)) < len(resolved_targets):
            raise DuplicateOutputError("Multiple split chunks resolved to the same output path.")

        staging_items: list[tuple[Path, Path, CollectionPlan]] = []

        try:
            # Stage all files
            for (plan, writer, _), norm_out in zip(plans_and_writers, resolved_targets, strict=True):
                dest_dir = norm_out.parent
                if not dest_dir.exists():
                    dest_dir.mkdir(parents=True, exist_ok=True)

                staging_fd, staging_path_str = tempfile.mkstemp(
                    dir=dest_dir,
                    prefix=".tmp_pdf_split_",
                    suffix=".staged",
                )
                staging_path = Path(staging_path_str)

                with os.fdopen(staging_fd, "wb") as f:
                    writer.write(f)
                    f.flush()
                    try:
                        os.fsync(f.fileno())
                    except (OSError, AttributeError):
                        pass

                # Validate staged PDF
                OutputTransaction.validate_staged_pdf(staging_path, plan.total_output_pages)
                staging_items.append((staging_path, norm_out, plan))

            # Commit all staged outputs
            committed_paths: list[Path] = []
            for staging_path, norm_out, _ in staging_items:
                if norm_out.exists() and overwrite_output:
                    staging_path.replace(norm_out)
                else:
                    try:
                        staging_path.rename(norm_out)
                    except OSError:
                        staging_path.replace(norm_out)
                committed_paths.append(norm_out)

            total_pages = sum(p.total_output_pages for p, _, _ in plans_and_writers)
            return OperationResult(
                output_paths=tuple(committed_paths),
                source_count=len(set(p.resolve() for p in input_paths)),
                output_page_count=total_pages,
                warnings=tuple(warnings),
            )

        except Exception as e:
            # Clean up all uncommitted staging files on failure
            for staging_path, _, _ in staging_items:
                if staging_path.exists():
                    try:
                        staging_path.unlink()
                    except OSError:
                        pass
            if isinstance(e, (AtomicWriteError, OutputValidationError, DuplicateOutputError)):
                raise
            raise AtomicWriteError(f"Failed to complete multi-output transaction: {e}") from e
