"""PDF reader wrapper and inspection utilities for PDF File Collector."""

from pathlib import Path

import pypdf

from pdf_file_collector.core.encryption import mask_password_in_text, resolve_password
from pdf_file_collector.core.exceptions import (
    IncorrectPasswordError,
    InvalidPdfError,
    PasswordRequiredError,
)
from pdf_file_collector.core.models import PdfDocumentInfo, PdfPageInfo
from pdf_file_collector.core.path_safety import validate_input_path


class PdfReaderService:
    """Service for opening, verifying, and reading PDF files."""

    @classmethod
    def open_pdf(
        cls,
        path: Path,
        password: str | None = None,
        password_env: str | None = None,
        strict: bool = False,
        prompt_interactive: bool = True,
    ) -> tuple[pypdf.PdfReader, str | None]:
        """Open and authenticate a PDF file."""
        validated_path = validate_input_path(path)

        try:
            reader = pypdf.PdfReader(str(validated_path), strict=strict)
        except Exception as e:
            raise InvalidPdfError(f"Failed to parse PDF '{path}': {e}") from e

        used_password: str | None = None

        if reader.is_encrypted:
            resolved_pwd = resolve_password(
                password_cli=password,
                password_env=password_env,
                prompt_if_interactive=prompt_interactive,
                prompt_message=f"Enter password for encrypted PDF '{path.name}': ",
            )

            if resolved_pwd is None:
                raise PasswordRequiredError(
                    f"PDF '{path}' is encrypted. Password required via --password or --password-env."
                )

            try:
                decrypt_res = reader.decrypt(resolved_pwd)
                if decrypt_res == 0:
                    raise IncorrectPasswordError(f"Incorrect password provided for encrypted PDF '{path}'.")
            except IncorrectPasswordError:
                raise
            except Exception as e:
                clean_err = mask_password_in_text(str(e), resolved_pwd)
                raise IncorrectPasswordError(f"Failed to decrypt PDF '{path}': {clean_err}") from None

            used_password = resolved_pwd

        try:
            _ = len(reader.pages)
        except Exception as e:
            msg = mask_password_in_text(str(e), used_password) if used_password else str(e)
            raise InvalidPdfError(f"Error accessing pages in PDF '{path}': {msg}") from e

        return reader, used_password

    @classmethod
    def get_document_info(
        cls,
        path: Path,
        pages_expr: str = "all",
        password: str | None = None,
        password_env: str | None = None,
        strict: bool = False,
    ) -> PdfDocumentInfo:
        """Inspect and return comprehensive document information."""
        reader, _ = cls.open_pdf(
            path=path,
            password=password,
            password_env=password_env,
            strict=strict,
        )

        file_size = path.stat().st_size
        pdf_version = reader.pdf_header if hasattr(reader, "pdf_header") else None
        total_pages = len(reader.pages)

        from pdf_file_collector.core.page_selection import PageSelectionParser

        sel_pages = PageSelectionParser.parse(pages_expr, total_pages, source_path=path)

        page_infos: list[PdfPageInfo] = []
        for p_num in sel_pages:
            p_idx = p_num - 1
            page = reader.pages[p_idx]
            box = page.mediabox
            width = float(box.width)
            height = float(box.height)
            rotation = int(page.get("/Rotate", 0) or 0)
            page_infos.append(
                PdfPageInfo(
                    page_number=p_num,
                    width=width,
                    height=height,
                    rotation=rotation,
                )
            )

        has_metadata = reader.metadata is not None and len(reader.metadata) > 0
        has_outlines = False
        try:
            has_outlines = len(reader.outline) > 0 if reader.outline else False
        except Exception:
            pass

        has_forms = False
        try:
            if reader.get_fields():
                has_forms = True
        except Exception:
            pass

        return PdfDocumentInfo(
            path=path,
            file_size_bytes=file_size,
            pdf_version=pdf_version,
            page_count=total_pages,
            is_encrypted=reader.is_encrypted,
            has_metadata=has_metadata,
            has_outlines=has_outlines,
            has_forms=has_forms,
            pages_info=tuple(page_infos),
        )
