# PDF File Collector

A non-destructive Python CLI for collecting, extracting, inserting, removing, reordering, reversing, splitting, merging, and composing pages from PDF files.

## Overview

`PDF File Collector` is a command-line utility designed for robust PDF page composition and manipulation. It operates purely on PDF page composition and never alters, redacts, annotates, crops, rotates, resizes, rasterizes, OCRs, watermarks, stamps, or otherwise edits the visible content of existing PDF pages.

This utility is part of the `Ilmars-Viksne/viUtility` repository and resides in `pdf-file-collector/`.

## Naming Conventions

- **Display Name:** `PDF File Collector`
- **Directory Name:** `pdf-file-collector`
- **Import Package:** `pdf_file_collector`
- **Distribution Name:** `pdf-file-collector`
- **CLI Executable:** `pdf-file-collector`

## Non-Destructive Guarantees

1. **Read-Only Sources:** Input PDF files are opened strictly for reading. They are never modified, overwritten, renamed, moved, deleted, or truncated.
2. **Distinct Output Required:** Every page-composition change writes to a new, distinct output path.
3. **Overwrite Protection:** Output files are protected against accidental overwrites by default. The `--overwrite-output` flag is required to replace an existing output file.
4. **Collision Prevention:** `--overwrite-output` will **never** permit overwriting an input file. Input-output collisions (including relative vs. absolute path matches, symlinks, and hard links) are detected and rejected.
5. **Atomic Output Transactions:** Output is written to a temporary staging file in the output destination directory, flushed to disk (`fsync`), re-opened, and verified for readable PDF structure and matching page count before being atomically renamed/committed to the final target path. If failure occurs during processing or validation, staging residue is removed cleanly without affecting pre-existing files or source inputs.
6. **Dry-Run Mode:** All write commands support `--dry-run`, which calculates and displays the proposed plan without creating any temporary files, staging files, output files, or directories.

## Non-Goals & Limitations

- No editing, adding, or removing page text or images.
- No OCR, watermarking, stamping, cropping, rotation, or page resizing.
- No form filling or form flattening.
- No digital signature creation or signature preservation guarantees (signatures remain on source pages but are marked as non-authoritative for the combined document).
- Does not preserve interactive bookmarks/outlines or named destinations across multi-source merges guarantees.
- Output encryption is out of scope.

## Requirements

- Python 3.11 or newer
- Dependencies: `pypdf`, `typer`, `rich`

## Installation

### From `pdf-file-collector/` directory:

#### Linux / macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

#### Windows PowerShell
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

After installation, verify with:
```bash
pdf-file-collector --help
pdf-file-collector --version
python -m pdf_file_collector --help
python -m pdf_file_collector --version
```

## Page-Selection Syntax

Page numbers in CLI arguments and user-facing messages are **1-based**.

- `1`: Page 1
- `1,3,5`: Pages 1, 3, and 5
- `1-5`: Pages 1 through 5
- `5-1`: Descending range: pages 5, 4, 3, 2, 1
- `odd`: All odd-numbered pages (1, 3, 5, ...)
- `even`: All even-numbered pages (2, 4, 6, ...)
- `all`: All pages
- `last`: The final page
- `1,last`: First and last pages
- `3-last`: Page 3 through final page
- `last-3`: Descending range from last page down to page 3
- `-5`: Pages 1 through 5
- `8-`: Page 8 through final page

Optional flag `--unique` eliminates duplicate pages while preserving order.

## Source-Specification Syntax

Commands accepting multiple input sources (`append`, `prepend`, `merge`, `collect`, `compose`, `validate`, `plan`) use `PATH::PAGE_EXPRESSION`:

```
cover.pdf::1
report.pdf::1-12
appendix.pdf::3,1,2
C:\Documents\Report.pdf::1-5
./documents/My Report.pdf::2-last
```

If `::PAGE_EXPRESSION` is omitted, it defaults to `all`.

## CLI Command Examples

### 1. `info`
Display PDF metadata, page count, encryption status, and page dimensions.
```bash
pdf-file-collector info input.pdf
pdf-file-collector info input.pdf --json
```

### 2. `extract`
Extract selected pages into a new PDF.
```bash
pdf-file-collector extract input.pdf --pages "1-3,8,last" --output selected.pdf
```

### 3. `remove`
Remove selected pages while saving retained pages to a new PDF.
```bash
pdf-file-collector remove input.pdf --pages "2,4,6" --output without_selected_pages.pdf
```

### 4. `reorder`
Reorder pages in a PDF.
```bash
pdf-file-collector reorder input.pdf --pages "3,1,2,4-last" --output reordered.pdf
```

### 5. `reverse`
Reverse page order.
```bash
pdf-file-collector reverse input.pdf --output reversed.pdf
pdf-file-collector reverse input.pdf --pages "2-8" --output reversed_selection.pdf
```

### 6. `insert`
Insert pages from a donor PDF into a base PDF.
```bash
pdf-file-collector insert report.pdf appendix.pdf --donor-pages "2-5" --before 10 --output report_with_appendix.pdf
pdf-file-collector insert report.pdf appendix.pdf --donor-pages "1,last" --after 3 --output report_with_appendix.pdf
```

### 7. `append`
Append donor PDF pages to a base PDF.
```bash
pdf-file-collector append report.pdf --add "appendix.pdf::1-3" --add "figures.pdf::2,5,last" --output complete.pdf
```

### 8. `prepend`
Prepend donor PDF pages before a base PDF.
```bash
pdf-file-collector prepend report.pdf --add "cover.pdf::1" --output complete.pdf
```

### 9. `merge`
Merge multiple PDFs or source specifications into one PDF.
```bash
pdf-file-collector merge part1.pdf part2.pdf part3.pdf --output merged.pdf
pdf-file-collector merge --source "part1.pdf::1-5" --source "part2.pdf::3-last" --output merged.pdf
```

### 10. `split`
Split a PDF by page count (`--every`), explicit ranges (`--ranges`), or split points (`--at`).
```bash
pdf-file-collector split input.pdf --every 10 --output-dir output_chunks
pdf-file-collector split input.pdf --ranges "1-3;4-8;9-last" --output-dir sections
pdf-file-collector split input.pdf --at "5,10,25" --output-dir sections
```

### 11. `collect` / `compose`
Collect pages from multiple source specifications into a new PDF.
```bash
pdf-file-collector collect --source "cover.pdf::1" --source "body.pdf::1-last" --source "appendix.pdf::2,1,3-last" --output final.pdf
pdf-file-collector compose --source "cover.pdf::1" --source "body.pdf::1-last" --source "appendix.pdf::2,1,3-last" --output final.pdf
```

### 12. `validate`
Validate PDF inputs and page specifications without creating files.
```bash
pdf-file-collector validate input.pdf --pages "1-4,last"
pdf-file-collector validate --source "a.pdf::1-4" --source "b.pdf::2-last"
```

### 13. `plan`
Display exact composition plan without executing writes.
```bash
pdf-file-collector plan --source "cover.pdf::1" --source "body.pdf::1-last" --output final.pdf
```

## Encryption & Passwords

Support for encrypted PDFs is available using:
- `--password TEXT`
- `--password-env ENV_VAR_NAME`
- Interactive hidden password prompt (active only when stdin is a TTY).

Passwords are never logged, printed, or emitted in JSON/tracebacks.

## Metadata Policy

- **Single-source operations** (`extract`, `remove`, `reorder`, `reverse`): Default policy is `keep`. Use `--metadata drop` to clear metadata.
- **Multi-source operations** (`collect`, `merge`, `append`, `prepend`, `insert`): Default policy is `drop`. Use `--metadata-from PATH` to select a metadata source.

## Exit Codes Reference

- `0`: Success
- `1`: Unexpected processing failure
- `2`: Invalid CLI usage / options
- `3`: Invalid input path, file, or PDF
- `4`: Invalid page selection or source specification
- `5`: Output conflict or unsafe collision
- `6`: Encryption or password failure
- `7`: Output write or validation failure

## Development & Verification

Run tests:
```bash
python -m pytest
```

Run tests with coverage:
```bash
python -m pytest --cov=pdf_file_collector --cov-report=term-missing
```

Run linter:
```bash
python -m ruff check .
```

Check formatting:
```bash
python -m ruff format --check .
```

Run static type checking:
```bash
python -m mypy src
```

## License

This project is licensed under the Apache License 2.0 - see [LICENSE](LICENSE) or the repository root [LICENSE](../LICENSE) for details.
