"""Tests for atomic CSV exports in the analytical pipeline."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.run_pipeline import export_query


class FakeCopy:
    """Simulate PostgreSQL COPY streaming."""

    def __init__(self, chunks, error=None):
        self.chunks = chunks
        self.error = error

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def __iter__(self):
        yield from self.chunks

        if self.error is not None:
            raise self.error


def make_connection(chunks, error=None):
    """Return a simulated database connection and cursor."""

    connection = MagicMock()
    cursor = MagicMock()

    connection.transaction.return_value.__enter__.return_value = None
    connection.cursor.return_value.__enter__.return_value = cursor

    cursor.copy.return_value = FakeCopy(
        chunks=chunks,
        error=error,
    )

    return connection, cursor


def test_successful_export_replaces_previous_csv(tmp_path):
    """A complete export must replace the previous CSV."""

    sql_path = tmp_path / "query.sql"
    output_path = tmp_path / "results.csv"

    sql_path.write_text(
        "SELECT 1 AS value;",
        encoding="utf-8",
    )
    output_path.write_text(
        "old,data\n",
        encoding="utf-8",
    )

    connection, cursor = make_connection(
        [b"value\n", b"1\n"],
    )

    export_query(
        connection,
        sql_path,
        output_path,
    )

    assert output_path.read_bytes() == b"value\n1\n"

    cursor.execute.assert_called_once_with("SET TRANSACTION READ ONLY")

    assert not list(tmp_path.glob("*.tmp"))


def test_failed_export_preserves_previous_csv(tmp_path):
    """A failed export must not overwrite valid existing data."""

    sql_path = tmp_path / "query.sql"
    output_path = tmp_path / "results.csv"

    sql_path.write_text(
        "SELECT 1 AS value;",
        encoding="utf-8",
    )

    previous_content = b"value\n999\n"

    output_path.write_bytes(previous_content)

    connection, _ = make_connection(
        chunks=[b"value\n", b"1\n"],
        error=RuntimeError("Simulated COPY failure"),
    )

    with pytest.raises(
        RuntimeError,
        match="Simulated COPY failure",
    ):
        export_query(
            connection,
            sql_path,
            output_path,
        )

    assert output_path.read_bytes() == previous_content

    assert not list(tmp_path.glob("*.tmp"))


def test_failed_export_does_not_create_final_csv(tmp_path):
    """A failed initial export must not leave a partial CSV."""

    sql_path = tmp_path / "query.sql"
    output_path = tmp_path / "results.csv"

    sql_path.write_text(
        "SELECT 1 AS value;",
        encoding="utf-8",
    )

    connection, _ = make_connection(
        chunks=[b"value\n"],
        error=RuntimeError("Interrupted export"),
    )

    with pytest.raises(
        RuntimeError,
        match="Interrupted export",
    ):
        export_query(
            connection,
            sql_path,
            output_path,
        )

    assert not output_path.exists()

    assert not list(tmp_path.glob("*.tmp"))


def test_empty_export_preserves_previous_csv(tmp_path):
    """An empty export must not replace existing valid data."""

    sql_path = tmp_path / "query.sql"
    output_path = tmp_path / "results.csv"

    sql_path.write_text(
        "SELECT 1 AS value;",
        encoding="utf-8",
    )

    previous_content = b"value\n123\n"

    output_path.write_bytes(previous_content)

    connection, _ = make_connection(chunks=[])

    with pytest.raises(
        RuntimeError,
        match="CSV export is empty",
    ):
        export_query(
            connection,
            sql_path,
            output_path,
        )

    assert output_path.read_bytes() == previous_content

    assert not list(tmp_path.glob("*.tmp"))


def test_export_creates_output_directory(tmp_path):
    """An export must create its destination directory."""

    sql_path = tmp_path / "query.sql"
    output_path = tmp_path / "nested" / "processed" / "results.csv"

    sql_path.write_text(
        "SELECT 1 AS value;",
        encoding="utf-8",
    )

    connection, _ = make_connection(
        chunks=[b"value\n", b"1\n"],
    )

    export_query(
        connection,
        sql_path,
        output_path,
    )

    assert output_path.read_bytes() == b"value\n1\n"
    assert output_path.parent.is_dir()


def test_empty_sql_is_rejected_before_export(tmp_path):
    """An empty SQL file must not create output files."""

    sql_path = tmp_path / "empty.sql"
    output_path = tmp_path / "results.csv"

    sql_path.write_text(
        "  ",
        encoding="utf-8",
    )

    connection = MagicMock()

    with pytest.raises(ValueError, match="Empty SQL"):
        export_query(
            connection,
            sql_path,
            output_path,
        )

    assert not output_path.exists()


def test_export_accepts_path_objects(tmp_path):
    """Export paths can be supplied as pathlib Path objects."""

    sql_path = Path(tmp_path / "query.sql")
    output_path = Path(tmp_path / "results.csv")

    sql_path.write_text(
        "SELECT 42 AS value;",
        encoding="utf-8",
    )

    connection, _ = make_connection(
        chunks=[b"value\n42\n"],
    )

    export_query(
        connection,
        sql_path,
        output_path,
    )

    assert (
        output_path.read_text(
            encoding="utf-8",
        )
        == "value\n42\n"
    )
