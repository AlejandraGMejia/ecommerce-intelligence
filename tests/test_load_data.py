
"""Unit tests for the Olist data loading pipeline."""

import csv
from pathlib import Path

import pytest

from src.load_data import count_csv_rows, validate_files


def test_count_csv_rows(tmp_path: Path) -> None:
    """CSV record counting excludes the header."""
    file_path = tmp_path / "sample.csv"

    with file_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["id", "name"])
        writer.writerow([1, "Product A"])
        writer.writerow([2, "Product B"])
        writer.writerow([3, "Product C"])

    assert count_csv_rows(file_path) == 3


def test_count_csv_rows_rejects_missing_header(
    tmp_path: Path,
) -> None:
    """Empty CSV files are rejected."""
    file_path = tmp_path / "empty.csv"
    file_path.touch()

    with pytest.raises(ValueError, match="Missing CSV header"):
        count_csv_rows(file_path)


def test_validate_files_rejects_missing_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing source file must stop the pipeline."""
    monkeypatch.setattr("src.load_data.DATA_DIR", tmp_path)

    with pytest.raises(FileNotFoundError):
        validate_files()
