"""CLI tests for text-file-collector."""

from __future__ import annotations

from text_file_collector import cli
from text_file_collector.core.entities import CollectionResult


class FakeCollectionService:
    """Fake service used by CLI tests."""

    def collect(self, request):
        return CollectionResult(
            files_seen=1,
            text_files_written=1,
            binary_files_skipped=0,
            output_file=request.output_file,
        )


def test_cli_run_command_uses_injected_fake_service(monkeypatch, tmp_path, capsys) -> None:
    """CLI run command parses arguments and reports success without real dependencies."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    output_file = tmp_path / "combined.txt"

    monkeypatch.setattr(cli, "build_collection_service", lambda settings: FakeCollectionService())

    exit_code = cli.main(
        [
            "run",
            "--input-dir",
            str(input_dir),
            "--output-file",
            str(output_file),
            "--log-level",
            "INFO",
        ],
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Done." in captured.out
    assert "Wrote 1 text file(s)" in captured.out
    assert captured.err == ""
