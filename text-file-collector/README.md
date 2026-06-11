# text-file-collector

A Python CLI utility that recursively scans a directory, skips binary files, and writes all readable text files into one combined output file.

Each collected file is written with its relative path followed by its content.

## Installation

From the `text-file-collector` folder:

```bash
pip install .
```

For editable development installation:

```bash
pip install -e ".[dev]"
```

## CLI Usage

Show help:

```bash
text-file-collector --help
```

Show version:

```bash
text-file-collector --version
```

Collect text files:

```bash
text-file-collector run --input-dir path/to/project --output-file combined_files.txt
```

Run with debug logging:

```bash
text-file-collector run --input-dir path/to/project --output-file combined_files.txt --log-level DEBUG
```

## Development Setup

```bash
python -m venv .venv
```

Activate the virtual environment.

On Windows PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

Install development dependencies:

```bash
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest
```

## Output Format

The generated output file contains repeated sections like this:

```text
================================================================================
FILE: src/example.py
================================================================================

print("Hello")
```
