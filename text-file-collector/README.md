# text-file-collector

A small Python CLI utility that recursively scans a directory and writes readable text files into one combined output file.

Binary files are skipped. Files that cannot be decoded with the selected encoding are skipped with warnings. Unreadable files are skipped with warnings. If the output file is inside the input directory, it is skipped during collection.

The output file is written via a temporary file and replaced only after collection succeeds, reducing the chance of leaving a partially written output file.

## Installation

```bash
pip install .
```

For editable development installation:

```bash
pip install -e ".[dev]"
```

## Usage

```bash
text-file-collector run --input-dir . --output-file combined_files.txt
```

With extra excludes:

```bash
text-file-collector run \
  --input-dir . \
  --output-file combined_files.txt \
  --exclude "*.log" \
  --exclude "data"
```

Without default excludes:

```bash
text-file-collector run \
  --input-dir . \
  --output-file combined_files.txt \
  --no-default-excludes
```

By default, the collector skips common project-noise directories and files such as `.git`, `.venv`, `__pycache__`, `node_modules`, `dist`, and `build`.

Use `--no-default-excludes` to disable this behavior.

With an explicit encoding:

```bash
text-file-collector run \
  --input-dir . \
  --output-file combined_files.txt \
  --encoding utf-8
```

Show help and version:

```bash
text-file-collector --help
text-file-collector --version
```

## Output Format

```text
================================================================================
FILE: src/example.py
================================================================================

print("Hello")
```

## Running Tests

```bash
pytest
```

```bash
pytest --cov=text_file_collector --cov-report=term-missing
```
