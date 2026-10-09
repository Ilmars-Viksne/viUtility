"""Tests for CLI commands, safety contract, non-destructive assertions, failure injection, and JSON errors."""

import json
from pathlib import Path

from conftest import compute_sha256
from typer.testing import CliRunner

from pdf_file_collector.cli import app

runner = CliRunner()


def test_cli_version() -> None:
    res = runner.invoke(app, ["--version"])
    assert res.exit_code == 0
    assert "PDF File Collector" in res.stdout


def test_cli_help() -> None:
    res = runner.invoke(app, ["--help"])
    assert res.exit_code == 0
    assert "PDF File Collector" in res.stdout


def test_info_command(sample_pdf_5p: Path) -> None:
    res = runner.invoke(app, ["info", str(sample_pdf_5p)])
    assert res.exit_code == 0
    assert "PDF Information:" in res.stdout
    assert "Total pages: 5" in res.stdout


def test_info_command_json(sample_pdf_5p: Path) -> None:
    res = runner.invoke(app, ["info", str(sample_pdf_5p), "--json"])
    assert res.exit_code == 0
    data = json.loads(res.stdout)
    assert data["operation"] == "info"
    assert data["total_pages"] == 5


def test_extract_command_non_destructive(sample_pdf_5p: Path, tmp_path: Path) -> None:
    sha_before = compute_sha256(sample_pdf_5p)
    mtime_before = sample_pdf_5p.stat().st_mtime
    out_pdf = tmp_path / "extracted.pdf"

    res = runner.invoke(
        app,
        ["extract", str(sample_pdf_5p), "--pages", "1,3,5", "--output", str(out_pdf)],
    )
    assert res.exit_code == 0
    assert out_pdf.exists()

    # Non-destructive assertion
    assert compute_sha256(sample_pdf_5p) == sha_before
    assert sample_pdf_5p.stat().st_mtime == mtime_before


def test_extract_refuses_input_collision(sample_pdf_5p: Path) -> None:
    res = runner.invoke(
        app,
        ["extract", str(sample_pdf_5p), "--pages", "1-2", "--output", str(sample_pdf_5p), "--overwrite-output"],
    )
    assert res.exit_code == 5  # ExitCode.OUTPUT_CONFLICT
    assert "Overwriting input files is strictly prohibited" in res.stderr


def test_remove_command(sample_pdf_5p: Path, tmp_path: Path) -> None:
    out_pdf = tmp_path / "removed.pdf"
    res = runner.invoke(
        app,
        ["remove", str(sample_pdf_5p), "--pages", "2,4", "--output", str(out_pdf)],
    )
    assert res.exit_code == 0
    assert out_pdf.exists()


def test_remove_refuses_all_pages(sample_pdf_5p: Path, tmp_path: Path) -> None:
    out_pdf = tmp_path / "removed.pdf"
    res = runner.invoke(
        app,
        ["remove", str(sample_pdf_5p), "--pages", "1-5", "--output", str(out_pdf)],
    )
    assert res.exit_code == 4  # ExitCode.INVALID_PAGE_SELECTION
    assert "Cannot remove all pages" in res.stderr


def test_reorder_command(sample_pdf_5p: Path, tmp_path: Path) -> None:
    out_pdf = tmp_path / "reordered.pdf"
    res = runner.invoke(
        app,
        ["reorder", str(sample_pdf_5p), "--pages", "3,1,2,5,4", "--output", str(out_pdf)],
    )
    assert res.exit_code == 0


def test_reverse_command(sample_pdf_5p: Path, tmp_path: Path) -> None:
    out_pdf = tmp_path / "reversed.pdf"
    res = runner.invoke(
        app,
        ["reverse", str(sample_pdf_5p), "--output", str(out_pdf)],
    )
    assert res.exit_code == 0


def test_insert_command(sample_pdf_5p: Path, sample_pdf_3p: Path, tmp_path: Path) -> None:
    out_pdf = tmp_path / "inserted.pdf"
    res = runner.invoke(
        app,
        [
            "insert",
            str(sample_pdf_5p),
            str(sample_pdf_3p),
            "--donor-pages",
            "1-2",
            "--after",
            "2",
            "--output",
            str(out_pdf),
        ],
    )
    assert res.exit_code == 0
    assert out_pdf.exists()


def test_append_command(sample_pdf_5p: Path, sample_pdf_3p: Path, tmp_path: Path) -> None:
    out_pdf = tmp_path / "appended.pdf"
    res = runner.invoke(
        app,
        [
            "append",
            str(sample_pdf_5p),
            "--add",
            f"{sample_pdf_3p}::1-2",
            "--output",
            str(out_pdf),
        ],
    )
    assert res.exit_code == 0


def test_prepend_command(sample_pdf_5p: Path, sample_pdf_3p: Path, tmp_path: Path) -> None:
    out_pdf = tmp_path / "prepended.pdf"
    res = runner.invoke(
        app,
        [
            "prepend",
            str(sample_pdf_5p),
            "--add",
            f"{sample_pdf_3p}::1-2",
            "--output",
            str(out_pdf),
        ],
    )
    assert res.exit_code == 0


def test_merge_command(sample_pdf_5p: Path, sample_pdf_3p: Path, tmp_path: Path) -> None:
    out_pdf = tmp_path / "merged.pdf"
    res = runner.invoke(
        app,
        [
            "merge",
            str(sample_pdf_5p),
            str(sample_pdf_3p),
            "--output",
            str(out_pdf),
        ],
    )
    assert res.exit_code == 0


def test_collect_and_compose_command(sample_pdf_5p: Path, sample_pdf_3p: Path, tmp_path: Path) -> None:
    out_pdf1 = tmp_path / "collected.pdf"
    res1 = runner.invoke(
        app,
        [
            "collect",
            "--source",
            f"{sample_pdf_5p}::1-2",
            "--source",
            f"{sample_pdf_3p}::last",
            "--output",
            str(out_pdf1),
        ],
    )
    assert res1.exit_code == 0

    out_pdf2 = tmp_path / "composed.pdf"
    res2 = runner.invoke(
        app,
        [
            "compose",
            "--source",
            f"{sample_pdf_5p}::1-2",
            "--source",
            f"{sample_pdf_3p}::last",
            "--output",
            str(out_pdf2),
        ],
    )
    assert res2.exit_code == 0


def test_split_command(sample_pdf_5p: Path, tmp_path: Path) -> None:
    out_dir = tmp_path / "split_chunks"
    res = runner.invoke(
        app,
        [
            "split",
            str(sample_pdf_5p),
            "--every",
            "2",
            "--output-dir",
            str(out_dir),
        ],
    )
    assert res.exit_code == 0
    assert out_dir.exists()
    assert len(list(out_dir.glob("*.pdf"))) == 3


def test_validate_command(sample_pdf_5p: Path) -> None:
    res = runner.invoke(app, ["validate", str(sample_pdf_5p), "--pages", "1-3"])
    assert res.exit_code == 0
    assert "Validation successful" in res.stdout


def test_plan_command(sample_pdf_5p: Path) -> None:
    res = runner.invoke(
        app,
        ["plan", "--source", f"{sample_pdf_5p}::1-2"],
    )
    assert res.exit_code == 0
    assert "Output page 1 <-" in res.stdout


def test_dry_run_creates_no_files(sample_pdf_5p: Path, tmp_path: Path) -> None:
    out_pdf = tmp_path / "non_existent.pdf"
    res = runner.invoke(
        app,
        ["extract", str(sample_pdf_5p), "--pages", "1-2", "--output", str(out_pdf), "--dry-run"],
    )
    assert res.exit_code == 0
    assert not out_pdf.exists()


def test_encrypted_pdf_handling(encrypted_pdf: Path, tmp_path: Path) -> None:
    out_pdf = tmp_path / "decrypted.pdf"

    # Without password
    res_no_pwd = runner.invoke(
        app,
        ["extract", str(encrypted_pdf), "--pages", "1-2", "--output", str(out_pdf)],
    )
    assert res_no_pwd.exit_code == 6  # ExitCode.ENCRYPTION_ERROR

    # With incorrect password
    res_bad_pwd = runner.invoke(
        app,
        ["extract", str(encrypted_pdf), "--pages", "1-2", "--output", str(out_pdf), "--password", "wrong"],
    )
    assert res_bad_pwd.exit_code == 6

    # With correct password
    res_good_pwd = runner.invoke(
        app,
        ["extract", str(encrypted_pdf), "--pages", "1-2", "--output", str(out_pdf), "--password", "secret123"],
    )
    assert res_good_pwd.exit_code == 0
    assert out_pdf.exists()


def test_json_error_output(sample_pdf_5p: Path) -> None:
    res = runner.invoke(
        app,
        ["extract", str(sample_pdf_5p), "--pages", "100", "--output", "out.pdf", "--json"],
    )
    assert res.exit_code == 4
    assert res.stdout == ""  # Stdout must be empty on failure with --json
    err_data = json.loads(res.stderr)
    assert err_data["status"] == "error"
    assert err_data["error_code"] == 4
