"""Load Olist customer reviews into PostgreSQL safely."""

import csv
import getpass
from pathlib import Path

import psycopg

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REVIEWS_CSV = PROJECT_ROOT / "data" / "raw" / "olist_order_reviews_dataset.csv"

DB_CONFIG = {
    "host": "localhost",
    "dbname": "ecommerce_db",
    "user": "ecommerce_user",
}

EXPECTED_COLUMNS = [
    "review_id",
    "order_id",
    "review_score",
    "review_comment_title",
    "review_comment_message",
    "review_creation_date",
    "review_answer_timestamp",
]

CHUNK_SIZE = 1024 * 1024


def validate_source() -> int:
    """Validate CSV header, row structure, and review scores."""
    if not REVIEWS_CSV.is_file():
        raise FileNotFoundError(f"Missing reviews CSV: {REVIEWS_CSV}")

    count = 0

    with REVIEWS_CSV.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)

        if reader.fieldnames != EXPECTED_COLUMNS:
            raise ValueError(f"Unexpected reviews CSV columns: {reader.fieldnames}")

        for row_number, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"Malformed reviews CSV record near row {row_number}")

            if not row["review_id"] or not row["order_id"]:
                raise ValueError(f"Missing review or order ID near row {row_number}")

            if row["review_score"] not in {"1", "2", "3", "4", "5"}:
                raise ValueError(f"Invalid review score near row {row_number}")

            count += 1

    if count == 0:
        raise ValueError("Reviews CSV contains no records.")

    return count


def get_review_count(conn: psycopg.Connection) -> int:
    """Get current review row count."""
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM reviews")
        result = cursor.fetchone()

    if result is None:
        raise RuntimeError("Could not count review records.")

    return result[0]


def validate_order_references(conn: psycopg.Connection) -> None:
    """Verify that every reviewed order exists in PostgreSQL."""
    source_order_ids = set()

    with REVIEWS_CSV.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)

        for row in reader:
            source_order_ids.add(row["order_id"])

    with conn.cursor() as cursor:
        cursor.execute("SELECT order_id FROM orders")
        database_order_ids = {row[0] for row in cursor.fetchall()}

    missing = source_order_ids - database_order_ids

    if missing:
        raise RuntimeError(
            f"{len(missing):,} reviewed orders are missing "
            "from PostgreSQL. No changes made."
        )

    print(f"Order references verified: {len(source_order_ids):,}")


def load_reviews(conn: psycopg.Connection) -> None:
    """Copy source records into the reviews table."""
    query = """
        COPY reviews (
            review_id,
            order_id,
            review_score,
            review_comment_title,
            review_comment_message,
            review_creation_date,
            review_answer_timestamp
        )
        FROM STDIN WITH (FORMAT CSV, HEADER TRUE)
    """

    with (
        conn.cursor() as cursor,
        REVIEWS_CSV.open("rb") as source,
        cursor.copy(query) as copy,
    ):
        while chunk := source.read(CHUNK_SIZE):
            copy.write(chunk)


def main() -> None:
    """Validate and transactionally load review records."""
    print("\n=== REVIEWS SOURCE VALIDATION ===")

    expected_count = validate_source()
    print(f"Source review records: {expected_count:,}")

    password = getpass.getpass("\nPostgreSQL password: ")

    with psycopg.connect(**DB_CONFIG, password=password) as conn:
        current_count = get_review_count(conn)

        if current_count == expected_count:
            print("\nReview row count already matches.")
            print("No changes made.")
            return

        if current_count > 0:
            raise RuntimeError(
                "The reviews table is not empty and its count "
                "does not match the source. No changes made."
            )

        print("\n=== REFERENTIAL INTEGRITY VALIDATION ===")
        validate_order_references(conn)

        print("\n=== LOADING REVIEWS ===")
        load_reviews(conn)

        loaded_count = get_review_count(conn)

        if loaded_count != expected_count:
            raise RuntimeError(
                f"Review count mismatch: expected {expected_count:,}, "
                f"found {loaded_count:,}"
            )

        print("\nReviews loaded successfully!")
        print(f"Records verified: {loaded_count:,}")
        print("Transaction will be committed.")


if __name__ == "__main__":
    main()
