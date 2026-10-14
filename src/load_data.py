
import getpass
from pathlib import Path

import psycopg


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "raw"

DB_NAME = "ecommerce_db"
DB_USER = "ecommerce_user"
DB_HOST = "localhost"

TABLES = [
    ("customers", "olist_customers_dataset.csv"),
    ("orders", "olist_orders_dataset.csv"),
    ("order_items", "olist_order_items_dataset.csv"),
]


def load_table(conn, table_name: str, filename: str) -> int:
    """Load a CSV into an existing PostgreSQL table."""
    file_path = DATA_DIR / filename

    if not file_path.is_file():
        raise FileNotFoundError(f"Missing CSV file: {file_path}")

    print(f"\nLoading {table_name}...")

    with conn.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        existing_rows = cursor.fetchone()[0]

        if existing_rows != 0:
            raise RuntimeError(
                f"Table {table_name} is not empty "
                f"({existing_rows:,} rows)."
            )

        with file_path.open("rb") as source:
            with cursor.copy(
                f"COPY {table_name} FROM STDIN "
                "WITH (FORMAT CSV, HEADER TRUE)"
            ) as copy:
                while chunk := source.read(1024 * 1024):
                    copy.write(chunk)

        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        loaded_rows = cursor.fetchone()[0]

    print(f"Loaded: {loaded_rows:,} rows")
    return loaded_rows


def main() -> None:
    password = getpass.getpass("PostgreSQL password: ")

    print("\nConnecting to PostgreSQL...")

    with psycopg.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=password,
    ) as conn:
        for table_name, filename in TABLES:
            load_table(conn, table_name, filename)

    print("\nAll tables loaded successfully!")


if __name__ == "__main__":
    main()
