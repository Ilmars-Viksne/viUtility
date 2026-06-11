"""Unit tests for the core collection service."""

from __future__ import annotations

from collections.abc import Iterable

from text_file_collector.core.entities import CollectionRequest, SourceFile
from text_file_collector.core.service import TextFileCollectionService


class FakeFileDiscoveryStrategy:
    """Fake file discovery strategy for unit tests."""

    def __init__(self, files: list[SourceFile]) -> None:
        self._files = files

    def discover(self, input_directory: str) -> Iterable[SourceFile]:
        return self._files


class FakeBinaryDetectionStrategy:
    """Fake binary detector based on relative path."""

    def __init__(self, binary_paths: set[str]) -> None:
        self._binary_paths = binary_paths

    def is_binary(self, source_file: SourceFile) -> bool:
        return source_file.relative_path in self._binary_paths


class FakeTextReaderStrategy:
    """Fake text reader based on relative path."""

    def __init__(self, contents: dict[str, str]) -> None:
        self._contents = contents

    def read_text(self, source_file: SourceFile) -> str:
        return self._contents[source_file.relative_path]


class FakeContentFormatterStrategy:
    """Fake formatter for unit tests."""

    def format_file(self, relative_path: str, content: str) -> str:
        return f"FILE:{relative_path}\n{content}\n"


class FakeOutputWriterStrategy:
    """Fake output writer that records sections."""

    def __init__(self) -> None:
        self.output_file: str | None = None
        self.sections: list[str] = []

    def write_sections(self, output_file: str, sections: Iterable[str]) -> int:
        self.output_file = output_file
        self.sections = list(sections)
        return len(self.sections)


def test_collects_only_non_binary_files() -> None:
    """Service writes only files not marked as binary."""
    writer = FakeOutputWriterStrategy()
    service = TextFileCollectionService(
        file_discovery=FakeFileDiscoveryStrategy(
            files=[
                SourceFile(identifier="/project/a.txt", relative_path="a.txt"),
                SourceFile(identifier="/project/image.png", relative_path="image.png"),
            ],
        ),
        binary_detector=FakeBinaryDetectionStrategy(binary_paths={"image.png"}),
        text_reader=FakeTextReaderStrategy(contents={"a.txt": "hello"}),
        content_formatter=FakeContentFormatterStrategy(),
        output_writer=writer,
    )

    result = service.collect(
        CollectionRequest(
            input_directory="/project",
            output_file="/project/combined.txt",
        ),
    )

    assert result.files_seen == 2
    assert result.text_files_written == 1
    assert result.binary_files_skipped == 1
    assert writer.sections == ["FILE:a.txt\nhello\n"]


def test_skips_output_file_when_discovered() -> None:
    """Service skips the output file if it appears during discovery."""
    writer = FakeOutputWriterStrategy()
    service = TextFileCollectionService(
        file_discovery=FakeFileDiscoveryStrategy(
            files=[
                SourceFile(identifier="/project/combined.txt", relative_path="combined.txt"),
                SourceFile(identifier="/project/src/main.py", relative_path="src/main.py"),
            ],
        ),
        binary_detector=FakeBinaryDetectionStrategy(binary_paths=set()),
        text_reader=FakeTextReaderStrategy(contents={"src/main.py": "print('hi')"}),
        content_formatter=FakeContentFormatterStrategy(),
        output_writer=writer,
    )

    result = service.collect(
        CollectionRequest(
            input_directory="/project",
            output_file="/project/combined.txt",
        ),
    )

    assert result.files_seen == 2
    assert result.text_files_written == 1
    assert result.binary_files_skipped == 0
    assert writer.sections == ["FILE:src/main.py\nprint('hi')\n"]
