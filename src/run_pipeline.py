"""Run validated e-commerce analytics exports and visualizations.

Features:
- Read-only PostgreSQL connections.
- BI data mart quality gate.
- Atomic CSV exports.
- Sequential analytical execution.
- Failure propagation.
- Environment-based database configuration.

Usage:
    python src/run_pipeline.py --check
    python src/run_pipeline.py
"""

import argparse
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import psycopg

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

QUALITY_GATE_PATH = PROJECT_ROOT / "sql" / "18_bi_quality_gate.sql"

EXPECTED_QUALITY_CHECKS = 9

ANALYSES = (
    {
        "name": "Customer Cohorts",
        "sql": PROJECT_ROOT / "sql" / "13_customer_cohorts.sql",
        "csv": PROCESSED_DIR / "customer_cohorts.csv",
        "script": PROJECT_ROOT / "src" / "visualize_cohorts.py",
    },
    {
        "name": "Customer RFM",
        "sql": PROJECT_ROOT / "sql" / "14_customer_rfm.sql",
        "csv": PROCESSED_DIR / "customer_rfm_segments.csv",
        "script": PROJECT_ROOT / "src" / "visualize_rfm.py",
    },
)

BI_EXPORTS = (
    {
        "name": "BI Monthly Sales",
        "sql": PROJECT_ROOT / "sql" / "17_bi_monthly_sales.sql",
        "csv": PROCESSED_DIR / "bi_monthly_sales.csv",
    },
    {
        "name": "BI Executive KPIs",
        "sql": PROJECT_ROOT / "sql" / "19_bi_executive_kpis.sql",
        "csv": PROCESSED_DIR / "bi_executive_kpis.csv",
    },
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


def validate_configuration() -> None:
    """Check the files required by the analytical pipeline."""

    required_files = [QUALITY_GATE_PATH]

    for analysis in ANALYSES:
        required_files.extend([analysis["sql"], analysis["script"]])

    for export in BI_EXPORTS:
        required_files.append(export["sql"])

    for path in required_files:
        if not path.is_file():
            raise FileNotFoundError(f"Required file not found: {path}")

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def get_database_connection() -> psycopg.Connection:
    """Connect using environment-based local configuration."""

    connection_kwargs = {
        "host": os.getenv("ECOMMERCE_DB_HOST", "localhost"),
        "port": int(os.getenv("ECOMMERCE_DB_PORT", "5432")),
        "dbname": os.getenv("ECOMMERCE_DB_NAME", "ecommerce_db"),
        "user": os.getenv("ECOMMERCE_DB_USER", "ecommerce_user"),
        "connect_timeout": 10,
        "autocommit": True,
        "options": "-c default_transaction_read_only=on",
    }

    password = os.getenv("ECOMMERCE_DB_PASSWORD")

    if password:
        connection_kwargs["password"] = password

    return psycopg.connect(**connection_kwargs)


def validate_database_connection() -> None:
    """Check connectivity without modifying database records."""

    logger.info("Checking PostgreSQL connection...")

    with (
        get_database_connection() as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute("SELECT 1")
        result = cursor.fetchone()

        if result is None or result[0] != 1:
            raise RuntimeError("Database connection validation failed.")

    logger.info("PostgreSQL connection: PASSED")


def read_sql(sql_path: Path) -> str:
    """Read a nonempty SQL query."""

    sql = sql_path.read_text(encoding="utf-8").strip()

    if not sql:
        raise ValueError(f"Empty SQL file: {sql_path}")

    return sql.rstrip(";").strip()


def validate_quality_gate(
    connection: psycopg.Connection,
) -> None:
    """Stop the pipeline when BI data mart checks do not pass."""

    logger.info("Running BI data mart quality gate...")

    sql = read_sql(QUALITY_GATE_PATH)

    with (
        connection.transaction(),
        connection.cursor() as cursor,
    ):
        cursor.execute("SET TRANSACTION READ ONLY")
        cursor.execute(sql)
        result = cursor.fetchone()

    if result is None or len(result) != 4:
        raise RuntimeError("Quality gate returned an unexpected result.")

    total_checks, passed_checks, failed_checks, status = result

    if (
        total_checks != EXPECTED_QUALITY_CHECKS
        or passed_checks != EXPECTED_QUALITY_CHECKS
        or failed_checks != 0
        or status != "PASSED"
    ):
        raise RuntimeError(
            "BI data mart quality gate FAILED: "
            f"total={total_checks}, "
            f"passed={passed_checks}, "
            f"failed={failed_checks}, "
            f"status={status}"
        )

    logger.info(
        "BI data mart quality gate: PASSED (%s/%s)",
        passed_checks,
        total_checks,
    )


def export_query(
    connection: psycopg.Connection,
    sql_path: Path,
    output_path: Path,
) -> None:
    """Export query results with atomic CSV replacement."""

    sql = read_sql(sql_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{output_path.stem}_",
            suffix=".tmp",
            dir=output_path.parent,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)

            with (
                connection.transaction(),
                connection.cursor() as cursor,
            ):
                cursor.execute("SET TRANSACTION READ ONLY")

                copy_sql = f"COPY ({sql}) TO STDOUT WITH (FORMAT CSV, HEADER TRUE)"

                with cursor.copy(copy_sql) as copy:
                    for chunk in copy:
                        temporary_file.write(chunk)

            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        if temporary_path.stat().st_size == 0:
            raise RuntimeError(f"CSV export is empty: {sql_path}")

        temporary_path.replace(output_path)

    except Exception:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()

        raise


def run_visualization(script_path: Path) -> None:
    """Run visualization using the current Python interpreter."""

    subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_ROOT,
        check=True,
    )


def run_pipeline() -> None:
    """Validate data and execute the configured export workflows."""

    logger.info("Starting E-Commerce Intelligence pipeline")

    validate_configuration()

    with get_database_connection() as connection:
        # Stop before exporting if data mart quality checks fail.
        validate_quality_gate(connection)

        for analysis in ANALYSES:
            logger.info("Processing: %s", analysis["name"])

            export_query(
                connection=connection,
                sql_path=analysis["sql"],
                output_path=analysis["csv"],
            )

            logger.info("CSV exported: %s", analysis["csv"].name)

            run_visualization(analysis["script"])

            logger.info("Completed: %s", analysis["name"])

        for export in BI_EXPORTS:
            logger.info("Processing: %s", export["name"])

            export_query(
                connection=connection,
                sql_path=export["sql"],
                output_path=export["csv"],
            )

            logger.info("BI CSV exported: %s", export["csv"].name)

    logger.info("Pipeline completed successfully")


def main() -> int:
    """Run a connection check or the complete analytical pipeline."""

    parser = argparse.ArgumentParser(
        description=("Run validated e-commerce analytical exports and visualizations.")
    )

    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Validate configuration and PostgreSQL "
            "connectivity without generating files."
        ),
    )

    args = parser.parse_args()

    try:
        validate_configuration()

        if args.check:
            validate_database_connection()
        else:
            run_pipeline()

    except (
        FileNotFoundError,
        OSError,
        ValueError,
        psycopg.Error,
        subprocess.CalledProcessError,
        RuntimeError,
    ):
        logger.exception("Pipeline failed")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
