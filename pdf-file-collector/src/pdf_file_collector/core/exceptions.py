"""Application exceptions and exit codes for PDF File Collector."""

from enum import IntEnum


class ExitCode(IntEnum):
    """Stable exit codes for PDF File Collector."""

    SUCCESS = 0
    UNEXPECTED_FAILURE = 1
    CLI_USAGE_ERROR = 2
    INVALID_INPUT = 3
    INVALID_PAGE_SELECTION = 4
    OUTPUT_CONFLICT = 5
    ENCRYPTION_ERROR = 6
    OUTPUT_WRITE_ERROR = 7


class PdfFileCollectorError(Exception):
    """Base exception for all PDF File Collector errors."""

    exit_code: ExitCode = ExitCode.UNEXPECTED_FAILURE

    def __init__(self, message: str, exit_code: ExitCode | None = None) -> None:
        super().__init__(message)
        if exit_code is not None:
            self.exit_code = exit_code


class InputFileNotFoundError(PdfFileCollectorError):
    """Raised when an input file does not exist."""

    exit_code = ExitCode.INVALID_INPUT


class InputPathError(PdfFileCollectorError):
    """Raised when an input path is invalid (e.g. is a directory)."""

    exit_code = ExitCode.INVALID_INPUT


class InvalidPdfError(PdfFileCollectorError):
    """Raised when a PDF file cannot be parsed or is corrupted."""

    exit_code = ExitCode.INVALID_INPUT


class EncryptedPdfError(PdfFileCollectorError):
    """Base error for encrypted PDF issues."""

    exit_code = ExitCode.ENCRYPTION_ERROR


class PasswordRequiredError(EncryptedPdfError):
    """Raised when a password is required but not provided."""

    exit_code = ExitCode.ENCRYPTION_ERROR


class IncorrectPasswordError(EncryptedPdfError):
    """Raised when an incorrect password is provided."""

    exit_code = ExitCode.ENCRYPTION_ERROR


class PageSelectionError(PdfFileCollectorError):
    """Raised when a page selection expression is invalid or malformed."""

    exit_code = ExitCode.INVALID_PAGE_SELECTION


class PageOutOfRangeError(PageSelectionError):
    """Raised when a selected page number is out of document bounds."""

    exit_code = ExitCode.INVALID_PAGE_SELECTION


class SourceSpecificationError(PdfFileCollectorError):
    """Raised when a source specification format is invalid."""

    exit_code = ExitCode.INVALID_PAGE_SELECTION


class OutputExistsError(PdfFileCollectorError):
    """Raised when an output file already exists and --overwrite-output is not set."""

    exit_code = ExitCode.OUTPUT_CONFLICT


class InputOutputCollisionError(PdfFileCollectorError):
    """Raised when an output file path resolves to an input file."""

    exit_code = ExitCode.OUTPUT_CONFLICT


class DuplicateOutputError(PdfFileCollectorError):
    """Raised when multiple outputs in a transaction target the same destination."""

    exit_code = ExitCode.OUTPUT_CONFLICT


class EmptyOutputError(PdfFileCollectorError):
    """Raised when an operation results in zero pages."""

    exit_code = ExitCode.INVALID_PAGE_SELECTION


class AtomicWriteError(PdfFileCollectorError):
    """Raised when writing or replacing a file fails during transaction commit."""

    exit_code = ExitCode.OUTPUT_WRITE_ERROR


class OutputValidationError(PdfFileCollectorError):
    """Raised when a staged output PDF fails validation checks."""

    exit_code = ExitCode.OUTPUT_WRITE_ERROR
