
"""Load and validate Olist e-commerce datasets in PostgreSQL."""

import argparse
import csv
import getpass
from pathlib import Path

import psycopg
from psycopg import sql

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "raw"

DB_NAME = "ecommerce_db"
DB_USER = "ecommerce_user"
DB_HOST = "localhost"

CHUNK_SIZE = 1024 * 1024

TABLES = {
    "customers": "olist_customers_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
}


def count_csv_rows(file_path: Path) -> int:
    """Count CSV records, excluding the header."""
    with file_path.open(
        "r", encoding="utf-8-sig", newline=""
    ) as source:
        reader = csv.reader(source)
        header = next(reader, None)

        if not header:
            raise ValueError(f"Missing CSV header: {file_path}")

        return sum(1 for _ in reader)


def validate_files() -> dict[str, int]:
    """Ensure all source files exist and contain records."""
    expected_counts = {}

    for table_name, filename in TABLES.items():
        file_path = DATA_DIR / filename

        if not file_path.is_file():
            raise FileNotFoundError(
                f"Source file not found: {file_path}"
            )

        count = count_csv_rows(file_path)

        if count == 0:
            raise ValueError(
                f"Source dataset is empty: {filename}"
            )

        expected_counts[table_name] = count

    return expected_counts


def get_database_count(
    conn: psycopg.Connection,
    table_name: str,
) -> int:
    """Retrieve the number of records in a database table."""
    query = sql.SQL("SELECT COUNT(*) FROM {}").format(
        sql.Identifier(table_name)
    )

    with conn.cursor() as cursor:
        cursor.execute(query)
        result = cursor.fetchone()

        if result is None:
            raise RuntimeError(
                f"Could not count records in {table_name}"
            )

        return result[0]


def load_table(
    conn: psycopg.Connection,
    table_name: str,
    filename: str,
) -> None:
    """Load CSV records using PostgreSQL COPY."""
    file_path = DATA_DIR / filename

    query = sql.SQL(
        "COPY {} FROM STDIN WITH (FORMAT CSV, HEADER TRUE)"
    ).format(sql.Identifier(table_name))

    with (
        conn.cursor() as cursor,
        file_path.open("rb") as source,
        cursor.copy(query) as copy,
    ):
        while chunk := source.read(CHUNK_SIZE):
            copy.write(chunk)


def get_current_counts(
    conn: psycopg.Connection,
) -> dict[str, int]:
    """Get record counts for all managed tables."""
    return {
        table_name: get_database_count(conn, table_name)
        for table_name in TABLES
    }


def truncate_tables(conn: psycopg.Connection) -> None:
    """Remove existing records from the three managed tables."""
    query = sql.SQL("TRUNCATE TABLE {}").format(
        sql.SQL(", ").join(
            sql.Identifier(table_name)
            for table_name in reversed(TABLES)
        )
    )

    with conn.cursor() as cursor:
        cursor.execute(query)


def run_pipeline(reload_data: bool = False) -> None:
    """Validate sources, load records, and verify row counts."""
    expected_counts = validate_files()

    print("\n=== SOURCE DATA VALIDATION ===")

    for table_name, count in expected_counts.items():
        print(f"{table_name}: {count:,} expected rows")

    password = getpass.getpass("\nPostgreSQL password: ")

    with psycopg.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=password,
    ) as conn:
        current_counts = get_current_counts(conn)

        counts_match = all(
            current_counts[name] == expected_counts[name]
            for name in TABLES
        )

        if not reload_data and counts_match:
            print("\nDatabase row counts already match.")
            print("No changes made.")
            return

        if not reload_data and any(current_counts.values()):
            raise RuntimeError(
                "Database contains records that do not match "
                "the expected source counts. "
                "No changes made. Investigate before reloading."
            )

        if reload_data:
            print("\nWARNING: Existing records will be replaced.")

            confirmation = input(
                "Type RELOAD to confirm: "
            )

            if confirmation != "RELOAD":
                print("Reload canceled. No changes made.")
                return

            truncate_tables(conn)

        print("\n=== LOADING DATA ===")

        for table_name, filename in TABLES.items():
            load_table(conn, table_name, filename)

            actual_count = get_database_count(conn, table_name)
            expected_count = expected_counts[table_name]

            if actual_count != expected_count:
                raise RuntimeError(
                    f"Row count mismatch in {table_name}: "
                    f"expected {expected_count:,}, "
                    f"found {actual_count:,}"
                )

            print(
                f"{table_name}: {actual_count:,} rows verified"
            )

        print("\nAll validation checks passed.")
        print("Transaction will be committed.")


def main() -> None:
    """Parse command-line arguments and run the pipeline."""
    parser = argparse.ArgumentParser(
        description=(
            "Load and validate Olist datasets in PostgreSQL."
        )
    )

    parser.add_argument(
        "--reload",
        action="store_true",
        help="Replace existing records after confirmation.",
    )

    args = parser.parse_args()

    run_pipeline(reload_data=args.reload)


if __name__ == "__main__":
    main()
