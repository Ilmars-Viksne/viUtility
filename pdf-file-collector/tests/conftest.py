"""Pytest fixtures and helpers for PDF File Collector test suite."""

import hashlib
from pathlib import Path

import pypdf
import pytest


def create_test_pdf(
    path: Path,
    num_pages: int = 5,
    title: str | None = None,
    password: str | None = None,
) -> Path:
    """Helper to programmatically generate fixture PDF files using pypdf."""
    writer = pypdf.PdfWriter()

    for _i in range(1, num_pages + 1):
        # Add blank page
        writer.add_blank_page(width=612, height=792)

    if title:
        writer.add_metadata({"/Title": title})

    if password:
        writer.encrypt(user_password=password, owner_password=password)

    with open(path, "wb") as f:
        writer.write(f)

    return path


def compute_sha256(path: Path) -> str:
    """Compute SHA-256 digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


@pytest.fixture
def sample_pdf_5p(tmp_path: Path) -> Path:
    """Fixture creating a 5-page unencrypted PDF."""
    pdf_path = tmp_path / "sample_5p.pdf"
    return create_test_pdf(pdf_path, num_pages=5, title="Sample Document")


@pytest.fixture
def sample_pdf_3p(tmp_path: Path) -> Path:
    """Fixture creating a 3-page unencrypted PDF."""
    pdf_path = tmp_path / "sample_3p.pdf"
    return create_test_pdf(pdf_path, num_pages=3, title="Sample Document 3P")


@pytest.fixture
def encrypted_pdf(tmp_path: Path) -> Path:
    """Fixture creating a 4-page encrypted PDF with password 'secret123'."""
    pdf_path = tmp_path / "encrypted.pdf"
    return create_test_pdf(pdf_path, num_pages=4, password="secret123")
