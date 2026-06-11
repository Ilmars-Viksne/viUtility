"""Custom exception hierarchy for text-file-collector."""


class TextFileCollectorError(Exception):
    """Base application exception."""


class InvalidCollectionRequestError(TextFileCollectorError):
    """Raised when a collection request is invalid."""


class CollectionWorkflowError(TextFileCollectorError):
    """Raised when the collection workflow cannot be completed."""


class InfrastructureError(TextFileCollectorError):
    """Raised when an infrastructure strategy fails."""


class InputDirectoryNotFoundError(InfrastructureError):
    """Raised when the configured input directory does not exist."""


class OutputWriteError(InfrastructureError):
    """Raised when the output writer cannot write the result."""
