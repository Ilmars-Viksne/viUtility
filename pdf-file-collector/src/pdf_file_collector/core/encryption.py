"""Password and encryption utilities for PDF File Collector."""

import os
import sys


def get_password_from_env(env_var_name: str) -> str | None:
    """Retrieve password from environment variable name."""
    return os.environ.get(env_var_name)


def resolve_password(
    password_cli: str | None = None,
    password_env: str | None = None,
    prompt_if_interactive: bool = True,
    prompt_message: str = "Enter PDF password: ",
) -> str | None:
    """Resolve password from CLI arg, environment variable, or interactive prompt if TTY.

    Never prompts if standard input is not a TTY.
    """
    if password_cli is not None:
        return password_cli

    if password_env is not None:
        password = get_password_from_env(password_env)
        if password is not None:
            return password

    if prompt_if_interactive and sys.stdin.isatty():
        try:
            import getpass

            return getpass.getpass(prompt_message)
        except (OSError, EOFError):
            pass

    return None


def mask_password_in_text(text: str, password: str) -> str:
    """Mask occurrences of password string in text if password is non-empty."""
    if password and password in text:
        return text.replace(password, "******")
    return text
