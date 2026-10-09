"""JSON output presentation layer."""

import json
import sys
from typing import Any


def print_json_stdout(data: dict[str, Any]) -> None:
    """Serialize and print JSON data to stdout."""
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    sys.stdout.write(json_str + "\n")
    sys.stdout.flush()


def print_json_stderr(data: dict[str, Any]) -> None:
    """Serialize and print JSON error data to stderr."""
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    sys.stderr.write(json_str + "\n")
    sys.stderr.flush()


def format_json_error(
    operation: str,
    error_code: int,
    error_type: str,
    message: str,
) -> dict[str, Any]:
    """Format structured machine-readable error object."""
    return {
        "operation": operation,
        "status": "error",
        "error_code": error_code,
        "error_type": error_type,
        "message": message,
    }
