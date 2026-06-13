"""CLI tests for text-file-collector."""

from __future__ import annotations

from pathlib import Path

from text_file_collector import cli


def test_cli_help(capsys) -> None:
    exit_code = cli.main(["--help"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "text-file-collector" in captured.out


def test_cli_version(capsys) -> None:
    exit_code = cli.main(["--version"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "text-file-collector" in captured.out


def test_cli_run_success(tmp_path, capsys) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "hello.txt").write_text("hello", encoding="utf-8")
    output_file = tmp_path / "combined.txt"

    exit_code = cli.main(
        [
            "run",
            "--input-dir",
            str(input_dir),
            "--output-file",
            str(output_file),
        ],
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Wrote 1 text file(s)" in captured.out
    assert output_file.exists()


def test_cli_invalid_input_dir_returns_2(tmp_path, capsys) -> None:
    exit_code = cli.main(
        [
            "run",
            "--input-dir",
            str(tmp_path / "missing"),
            "--output-file",
            str(tmp_path / "combined.txt"),
        ],
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Input directory does not exist" in captured.err


def test_cli_output_file_existing_directory_returns_2(tmp_path, capsys) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    exit_code = cli.main(
        [
            "run",
            "--input-dir",
            str(input_dir),
            "--output-file",
            str(output_dir),
        ],
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "existing directory" in captured.err


def test_cli_invalid_log_level_returns_2(tmp_path, capsys) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()

    exit_code = cli.main(
        [
            "run",
            "--input-dir",
            str(input_dir),
            "--output-file",
            str(tmp_path / "combined.txt"),
            "--log-level",
            "LOUD",
        ],
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Unsupported log level" in captured.err


def test_cli_invalid_encoding_returns_2(tmp_path, capsys) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()

    exit_code = cli.main(
        [
            "run",
            "--input-dir",
            str(input_dir),
            "--output-file",
            str(tmp_path / "combined.txt"),
            "--encoding",
            "not-a-real-encoding",
        ],
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Unsupported encoding" in captured.err


def test_cli_no_command_returns_2(capsys) -> None:
    exit_code = cli.main([])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "required" in captured.err


def test_cli_exclude_option_skips_file(tmp_path) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "keep.txt").write_text("keep", encoding="utf-8")
    (input_dir / "skip.log").write_text("skip", encoding="utf-8")
    output_file = tmp_path / "combined.txt"

    exit_code = cli.main(
        [
            "run",
            "--input-dir",
            str(input_dir),
            "--output-file",
            str(output_file),
            "--exclude",
            "*.log",
        ],
    )

    assert exit_code == 0
    assert "keep" in output_file.read_text(encoding="utf-8")
    assert "skip" not in output_file.read_text(encoding="utf-8")
