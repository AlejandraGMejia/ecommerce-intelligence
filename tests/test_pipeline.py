"""Automated tests for the analytical pipeline orchestrator."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import psycopg
import pytest

from src import run_pipeline


def create_mock_connection(result=(1,)):
    """Build a database mock compatible with context managers."""

    connection = MagicMock()
    cursor = MagicMock()

    connection.__enter__.return_value = connection
    connection.cursor.return_value.__enter__.return_value = cursor
    connection.transaction.return_value.__enter__.return_value = None

    cursor.fetchone.return_value = result

    return connection, cursor


def test_configuration_files_exist():
    """All required SQL files and scripts must exist."""

    run_pipeline.validate_configuration()

    for analysis in run_pipeline.ANALYSES:
        assert analysis["sql"].is_file()
        assert analysis["script"].is_file()

    for export in run_pipeline.BI_EXPORTS:
        assert export["sql"].is_file()

    assert run_pipeline.QUALITY_GATE_PATH.is_file()


def test_pipeline_has_expected_analyses():
    """The pipeline must include customer cohorts and RFM."""

    names = {analysis["name"] for analysis in run_pipeline.ANALYSES}

    assert names == {
        "Customer Cohorts",
        "Customer RFM",
    }


def test_pipeline_has_monthly_bi_export():
    """The pipeline must include the monthly BI dataset."""

    names = {export["name"] for export in run_pipeline.BI_EXPORTS}

    assert "BI Monthly Sales" in names


def test_database_connection_uses_configuration(monkeypatch):
    """Connection settings must use environment variables."""

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
    assert kwargs["autocommit"] is True
    assert "default_transaction_read_only=on" in kwargs["options"]


def test_database_connection_validation():
    """A successful SELECT 1 validates database connectivity."""

    connection, cursor = create_mock_connection(result=(1,))

    with patch(
        "src.run_pipeline.get_database_connection",
        return_value=connection,
    ):
        run_pipeline.validate_database_connection()

    cursor.execute.assert_called_once_with("SELECT 1")


def test_invalid_database_response_is_rejected():
    """Unexpected database health-check results must fail."""

    connection, _ = create_mock_connection(result=(0,))

    with (
        patch(
            "src.run_pipeline.get_database_connection",
            return_value=connection,
        ),
        pytest.raises(RuntimeError, match="validation failed"),
    ):
        run_pipeline.validate_database_connection()


def test_quality_gate_passes():
    """Nine successful quality checks must be accepted."""

    connection, cursor = create_mock_connection(result=(9, 9, 0, "PASSED"))

    run_pipeline.validate_quality_gate(connection)

    assert cursor.execute.call_count == 2
    cursor.execute.assert_any_call("SET TRANSACTION READ ONLY")


def test_quality_gate_rejects_failed_checks():
    """Failed quality checks must stop pipeline execution."""

    connection, _ = create_mock_connection(result=(9, 8, 1, "FAILED"))

    with pytest.raises(RuntimeError, match="quality gate FAILED"):
        run_pipeline.validate_quality_gate(connection)


def test_quality_gate_rejects_missing_checks():
    """The quality gate must require all nine checks."""

    connection, _ = create_mock_connection(result=(8, 8, 0, "PASSED"))

    with pytest.raises(RuntimeError, match="quality gate FAILED"):
        run_pipeline.validate_quality_gate(connection)


def test_quality_gate_rejects_unexpected_result():
    """Malformed quality gate results must be rejected."""

    connection, _ = create_mock_connection(result=None)

    with pytest.raises(RuntimeError, match="unexpected result"):
        run_pipeline.validate_quality_gate(connection)


def test_visualization_uses_python_interpreter():
    """Visualizations must run with the active interpreter."""

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
    """An empty SQL file must not produce exports."""

    sql_path = tmp_path / "empty.sql"
    output_path = tmp_path / "output.csv"

    sql_path.write_text("", encoding="utf-8")

    connection = MagicMock()

    with pytest.raises(ValueError, match="Empty SQL"):
        run_pipeline.export_query(
            connection,
            sql_path,
            output_path,
        )

    assert not output_path.exists()


def test_pipeline_stops_when_quality_gate_fails():
    """A failed gate must prevent all exports and visualizations."""

    connection, _ = create_mock_connection()

    with (
        patch(
            "src.run_pipeline.get_database_connection",
            return_value=connection,
        ),
        patch(
            "src.run_pipeline.validate_quality_gate",
            side_effect=RuntimeError("Quality gate failed"),
        ),
        patch("src.run_pipeline.export_query") as mock_export,
        patch(
            "src.run_pipeline.run_visualization",
        ) as mock_visualization,
        pytest.raises(RuntimeError, match="Quality gate failed"),
    ):
        run_pipeline.run_pipeline()

    mock_export.assert_not_called()
    mock_visualization.assert_not_called()


def test_pipeline_stops_when_export_fails():
    """A failed SQL export must prevent visualization execution."""

    connection, _ = create_mock_connection()

    with (
        patch(
            "src.run_pipeline.get_database_connection",
            return_value=connection,
        ),
        patch("src.run_pipeline.validate_quality_gate"),
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


def test_pipeline_processes_every_analysis_and_bi_export():
    """Successful runs must execute every configured step."""

    connection, _ = create_mock_connection()

    with (
        patch(
            "src.run_pipeline.get_database_connection",
            return_value=connection,
        ),
        patch(
            "src.run_pipeline.validate_quality_gate",
        ) as mock_gate,
        patch(
            "src.run_pipeline.export_query",
        ) as mock_export,
        patch(
            "src.run_pipeline.run_visualization",
        ) as mock_visualization,
    ):
        run_pipeline.run_pipeline()

    expected_exports = len(run_pipeline.ANALYSES) + len(run_pipeline.BI_EXPORTS)

    mock_gate.assert_called_once_with(connection)
    assert mock_export.call_count == expected_exports
    expected_visualizations = len(run_pipeline.ANALYSES) + sum(
        "script" in export for export in run_pipeline.BI_EXPORTS
    )
    assert mock_visualization.call_count == expected_visualizations


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
