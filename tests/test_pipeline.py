"""Automated tests for the analytical pipeline orchestrator."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import psycopg
import pytest

from src import run_pipeline


def test_configuration_files_exist():
    """All configured SQL queries and scripts must exist."""

    for analysis in run_pipeline.ANALYSES:
        assert analysis["sql"].is_file()
        assert analysis["script"].is_file()


def test_pipeline_has_expected_analyses():
    """The initial pipeline must contain cohorts and RFM."""

    names = {analysis["name"] for analysis in run_pipeline.ANALYSES}

    assert names == {
        "Customer Cohorts",
        "Customer RFM",
    }


def test_database_connection_uses_configuration(monkeypatch):
    """Database connection settings must use environment variables."""

    monkeypatch.setenv("ECOMMERCE_DB_HOST", "localhost")
    monkeypatch.setenv("ECOMMERCE_DB_PORT", "5432")
    monkeypatch.setenv("ECOMMERCE_DB_NAME", "ecommerce_db")
    monkeypatch.setenv("ECOMMERCE_DB_USER", "ecommerce_user")
    monkeypatch.setenv("ECOMMERCE_DB_PASSWORD", "test-password")

    with patch("src.run_pipeline.psycopg.connect") as mock_connect:
        run_pipeline.get_database_connection()

    kwargs = mock_connect.call_args.kwargs

    assert kwargs["host"] == "localhost"
    assert kwargs["port"] == 5432
    assert kwargs["dbname"] == "ecommerce_db"
    assert kwargs["user"] == "ecommerce_user"
    assert kwargs["password"] == "test-password"
    assert kwargs["connect_timeout"] == 10


def create_mock_connection(result=(1,)):
    """Build a mock connection compatible with context managers."""

    mock_connection = MagicMock()
    mock_cursor = MagicMock()

    mock_connection.__enter__.return_value = mock_connection
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

    mock_cursor.fetchone.return_value = result

    return mock_connection, mock_cursor


def test_database_connection_validation():
    """A successful SELECT 1 validates database connectivity."""

    mock_connection, mock_cursor = create_mock_connection(result=(1,))

    with patch(
        "src.run_pipeline.get_database_connection",
        return_value=mock_connection,
    ):
        run_pipeline.validate_database_connection()

    mock_cursor.execute.assert_called_once_with("SELECT 1")


def test_invalid_database_response_is_rejected():
    """Unexpected database health-check results must fail."""

    mock_connection, _ = create_mock_connection(result=(0,))

    with (
        patch(
            "src.run_pipeline.get_database_connection",
            return_value=mock_connection,
        ),
        pytest.raises(
            RuntimeError,
            match="validation failed",
        ),
    ):
        run_pipeline.validate_database_connection()


def test_visualization_uses_python_interpreter():
    """Visualization scripts must run with the active interpreter."""

    script_path = Path("/tmp/example_visualization.py")

    with patch("src.run_pipeline.subprocess.run") as mock_run:
        run_pipeline.run_visualization(script_path)

    args, kwargs = mock_run.call_args

    assert args[0][0] == run_pipeline.sys.executable
    assert args[0][1] == str(script_path)
    assert kwargs["check"] is True
    assert kwargs["cwd"] == run_pipeline.PROJECT_ROOT


def test_visualization_failure_is_propagated():
    """A failed visualization must stop the pipeline."""

    script_path = Path("/tmp/failing_visualization.py")

    with (
        patch(
            "src.run_pipeline.subprocess.run",
            side_effect=subprocess.CalledProcessError(
                1,
                ["python", str(script_path)],
            ),
        ),
        pytest.raises(subprocess.CalledProcessError),
    ):
        run_pipeline.run_visualization(script_path)


def test_export_query_rejects_empty_sql(tmp_path):
    """Empty SQL files must not produce exports."""

    sql_path = tmp_path / "empty.sql"
    output_path = tmp_path / "output.csv"

    sql_path.write_text("", encoding="utf-8")

    mock_connection = MagicMock()

    with pytest.raises(ValueError, match="Empty SQL"):
        run_pipeline.export_query(
            mock_connection,
            sql_path,
            output_path,
        )

    assert not output_path.exists()


def test_pipeline_stops_when_export_fails():
    """A failed SQL export must prevent visualization execution."""

    mock_connection = MagicMock()

    with (
        patch(
            "src.run_pipeline.get_database_connection",
            return_value=mock_connection,
        ),
        patch(
            "src.run_pipeline.export_query",
            side_effect=psycopg.OperationalError("Simulated database error"),
        ),
        patch(
            "src.run_pipeline.run_visualization",
        ) as mock_visualization,
        pytest.raises(
            psycopg.OperationalError,
            match="Simulated database error",
        ),
    ):
        run_pipeline.run_pipeline()

    mock_visualization.assert_not_called()


def test_pipeline_processes_every_analysis():
    """Successful execution must export and visualize each analysis."""

    mock_connection = MagicMock()

    with (
        patch(
            "src.run_pipeline.get_database_connection",
            return_value=mock_connection,
        ),
        patch(
            "src.run_pipeline.export_query",
        ) as mock_export,
        patch(
            "src.run_pipeline.run_visualization",
        ) as mock_visualization,
    ):
        run_pipeline.run_pipeline()

    assert mock_export.call_count == len(run_pipeline.ANALYSES)
    assert mock_visualization.call_count == len(run_pipeline.ANALYSES)


def test_check_mode_does_not_run_exports(monkeypatch):
    """The --check option must not execute analytical exports."""

    monkeypatch.setattr(
        "sys.argv",
        ["run_pipeline.py", "--check"],
    )

    with (
        patch("src.run_pipeline.validate_configuration"),
        patch(
            "src.run_pipeline.validate_database_connection",
        ) as mock_validate,
        patch(
            "src.run_pipeline.run_pipeline",
        ) as mock_pipeline,
    ):
        result = run_pipeline.main()

    assert result == 0
    mock_validate.assert_called_once()
    mock_pipeline.assert_not_called()
