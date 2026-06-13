"""Filesystem tests for the collector."""

from __future__ import annotations

import os
import sys

import pytest

import text_file_collector.collector as collector
from text_file_collector.collector import (
    DEFAULT_EXCLUDES,
    CollectionOptions,
    collect_text_files,
)
from text_file_collector.exceptions import TextFileCollectorError


def test_collects_text_files_recursively(tmp_path) -> None:
    input_dir = tmp_path / "input"
    nested = input_dir / "src"
    nested.mkdir(parents=True)
    (input_dir / "README.md").write_text("readme", encoding="utf-8")
    (nested / "app.py").write_text("print('hi')", encoding="utf-8")

    result = collect_text_files(CollectionOptions(input_dir, tmp_path / "combined.txt"))
    output = result.output_file.read_text(encoding="utf-8")

    assert result.files_written == 2
    assert "FILE: README.md" in output
    assert "FILE: src/app.py" in output


def test_output_format_matches_expected(tmp_path) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "a.txt").write_text("hello\n", encoding="utf-8")

    result = collect_text_files(CollectionOptions(input_dir, tmp_path / "combined.txt"))

    assert result.output_file.read_text(encoding="utf-8") == (
        "================================================================================\n"
        "FILE: a.txt\n"
        "================================================================================\n"
        "\n"
        "hello\n"
    )


def test_preserves_multiple_trailing_newlines(tmp_path) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "a.txt").write_text("hello\n\n", encoding="utf-8")

    result = collect_text_files(CollectionOptions(input_dir, tmp_path / "combined.txt"))

    assert result.output_file.read_text(encoding="utf-8") == (
        "================================================================================\n"
        "FILE: a.txt\n"
        "================================================================================\n"
        "\n"
        "hello\n\n"
    )


def test_adds_newline_for_file_without_final_newline(tmp_path) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "a.txt").write_text("hello", encoding="utf-8")

    result = collect_text_files(CollectionOptions(input_dir, tmp_path / "combined.txt"))

    assert result.output_file.read_text(encoding="utf-8").endswith("hello\n")
    assert not result.output_file.read_text(encoding="utf-8").endswith("hello\n\n")


def test_deterministic_output_order(tmp_path) -> None:
    input_dir = tmp_path / "input"
    nested = input_dir / "nested"
    nested.mkdir(parents=True)
    (input_dir / "b.txt").write_text("b", encoding="utf-8")
    (input_dir / "a.txt").write_text("a", encoding="utf-8")
    (nested / "d.txt").write_text("d", encoding="utf-8")
    (nested / "c.txt").write_text("c", encoding="utf-8")

    result = collect_text_files(CollectionOptions(input_dir, tmp_path / "combined.txt"))
    output = result.output_file.read_text(encoding="utf-8")

    assert output.index("FILE: a.txt") < output.index("FILE: b.txt")
    assert output.index("FILE: b.txt") < output.index("FILE: nested/c.txt")
    assert output.index("FILE: nested/c.txt") < output.index("FILE: nested/d.txt")


def test_skips_binary_file_with_null_byte(tmp_path) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "binary.bin").write_bytes(b"abc\x00def")
    (input_dir / "text.txt").write_text("text", encoding="utf-8")

    result = collect_text_files(CollectionOptions(input_dir, tmp_path / "combined.txt"))
    output = result.output_file.read_text(encoding="utf-8")

    assert result.files_seen == 2
    assert result.binary_files_skipped == 1
    assert "binary.bin" not in output
    assert "text.txt" in output


def test_skips_undecodable_file(tmp_path, caplog) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "bad.txt").write_bytes(b"\xff\xfe\xfa")
    (input_dir / "good.txt").write_text("good", encoding="utf-8")

    result = collect_text_files(CollectionOptions(input_dir, tmp_path / "combined.txt"))

    assert result.decode_errors_skipped == 1
    assert "good.txt" in result.output_file.read_text(encoding="utf-8")
    assert "Skipping undecodable file" in caplog.text


def test_skips_unreadable_file_if_possible(tmp_path, monkeypatch) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    unreadable = input_dir / "unreadable.txt"
    unreadable.write_text("secret", encoding="utf-8")
    (input_dir / "good.txt").write_text("good", encoding="utf-8")

    original_is_binary_file = collector.is_binary_file

    def fake_is_binary_file(path):
        if path == unreadable:
            return None
        return original_is_binary_file(path)

    monkeypatch.setattr(collector, "is_binary_file", fake_is_binary_file)

    result = collect_text_files(CollectionOptions(input_dir, tmp_path / "combined.txt"))

    assert result.read_errors_skipped == 1
    assert "good.txt" in result.output_file.read_text(encoding="utf-8")


def test_skips_output_file_inside_input_directory(tmp_path) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "a.txt").write_text("a", encoding="utf-8")
    output_file = input_dir / "combined.txt"
    output_file.write_text("old", encoding="utf-8")

    result = collect_text_files(CollectionOptions(input_dir, output_file))
    output = output_file.read_text(encoding="utf-8")

    assert result.files_seen == 1
    assert "FILE: combined.txt" not in output
    assert "FILE: a.txt" in output


def test_creates_output_parent_directory(tmp_path) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "a.txt").write_text("a", encoding="utf-8")
    output_file = tmp_path / "missing" / "combined.txt"

    result = collect_text_files(CollectionOptions(input_dir, output_file))

    assert result.output_file == output_file.resolve()
    assert output_file.exists()


def test_default_excludes_skip_git_venv_pycache_node_modules(tmp_path) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    for directory in [".git", ".venv", "__pycache__", "node_modules"]:
        excluded = input_dir / directory
        excluded.mkdir()
        (excluded / "hidden.txt").write_text(directory, encoding="utf-8")
    (input_dir / "keep.txt").write_text("keep", encoding="utf-8")

    result = collect_text_files(CollectionOptions(input_dir, tmp_path / "combined.txt"))
    output = result.output_file.read_text(encoding="utf-8")

    assert result.files_seen == 1
    assert "keep.txt" in output
    assert "hidden.txt" not in output


def test_user_excludes_skip_matching_files(tmp_path) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "a.txt").write_text("a", encoding="utf-8")
    (input_dir / "debug.log").write_text("debug", encoding="utf-8")

    result = collect_text_files(
        CollectionOptions(input_dir, tmp_path / "combined.txt", excludes=DEFAULT_EXCLUDES + ("*.log",)),
    )
    output = result.output_file.read_text(encoding="utf-8")

    assert result.files_written == 1
    assert "a.txt" in output
    assert "debug.log" not in output


def test_relative_path_exclude_pattern_skips_matching_files(tmp_path) -> None:
    input_dir = tmp_path / "input"
    generated = input_dir / "src" / "generated"
    manual = input_dir / "src" / "manual"
    generated.mkdir(parents=True)
    manual.mkdir(parents=True)
    (generated / "a.txt").write_text("generated", encoding="utf-8")
    (manual / "b.txt").write_text("manual", encoding="utf-8")

    result = collect_text_files(
        CollectionOptions(
            input_dir,
            tmp_path / "combined.txt",
            excludes=DEFAULT_EXCLUDES + ("src/generated/*",),
        ),
    )
    output = result.output_file.read_text(encoding="utf-8")

    assert "FILE: src/generated/a.txt" not in output
    assert "FILE: src/manual/b.txt" in output


def test_no_default_excludes_disables_default_excludes(tmp_path) -> None:
    input_dir = tmp_path / "input"
    git_dir = input_dir / ".git"
    git_dir.mkdir(parents=True)
    (git_dir / "config").write_text("config", encoding="utf-8")

    result = collect_text_files(CollectionOptions(input_dir, tmp_path / "combined.txt", excludes=()))
    output = result.output_file.read_text(encoding="utf-8")

    assert result.files_written == 1
    assert "FILE: .git/config" in output


def test_empty_input_directory_creates_empty_output_file(tmp_path) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()

    result = collect_text_files(CollectionOptions(input_dir, tmp_path / "combined.txt"))

    assert result.files_seen == 0
    assert result.output_file.read_text(encoding="utf-8") == ""


def test_result_counts_are_correct(tmp_path) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "a.txt").write_text("a", encoding="utf-8")
    (input_dir / "b.bin").write_bytes(b"\x00")
    (input_dir / "c.txt").write_bytes(b"\xff")

    result = collect_text_files(CollectionOptions(input_dir, tmp_path / "combined.txt"))

    assert result.files_seen == 3
    assert result.files_written == 1
    assert result.files_skipped == 2
    assert result.binary_files_skipped == 1
    assert result.decode_errors_skipped == 1
    assert result.read_errors_skipped == 0


def test_atomic_write_does_not_replace_existing_file_on_failure(tmp_path, monkeypatch) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "a.txt").write_text("a", encoding="utf-8")
    output_file = tmp_path / "combined.txt"
    output_file.write_text("old", encoding="utf-8")

    def fail_replace(source, target):
        raise OSError("replace failed")

    monkeypatch.setattr(collector, "_replace_file", fail_replace)

    with pytest.raises(TextFileCollectorError):
        collect_text_files(CollectionOptions(input_dir, output_file))

    assert output_file.read_text(encoding="utf-8") == "old"
    assert list(tmp_path.glob(".text-file-collector-*.tmp")) == []


def test_output_directory_creation_failure_is_wrapped(tmp_path, monkeypatch) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "a.txt").write_text("a", encoding="utf-8")
    output_file = tmp_path / "missing" / "combined.txt"

    original_mkdir = collector.Path.mkdir

    def fail_mkdir(self, parents=False, exist_ok=False):
        if self == output_file.parent:
            raise OSError("mkdir failed")
        return original_mkdir(self, parents=parents, exist_ok=exist_ok)

    monkeypatch.setattr(collector.Path, "mkdir", fail_mkdir)

    with pytest.raises(TextFileCollectorError, match="Could not create output directory"):
        collect_text_files(CollectionOptions(input_dir, output_file))


@pytest.mark.skipif(sys.platform == "win32", reason="chmod unreadable behavior differs on Windows")
def test_skips_unreadable_file_with_permissions_when_supported(tmp_path) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    unreadable = input_dir / "unreadable.txt"
    unreadable.write_text("secret", encoding="utf-8")
    unreadable.chmod(0)

    try:
        result = collect_text_files(CollectionOptions(input_dir, tmp_path / "combined.txt"))
    finally:
        unreadable.chmod(0o600)

    if os.geteuid() != 0:
        assert result.read_errors_skipped == 1
