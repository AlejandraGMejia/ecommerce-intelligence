"""Load and validate Olist product data in PostgreSQL."""

import csv
import getpass
from pathlib import Path

import psycopg

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"

PRODUCTS_CSV = RAW_DIR / "olist_products_dataset.csv"
CATEGORIES_CSV = RAW_DIR / "product_category_name_translation.csv"

DB_CONFIG = {
    "host": "localhost",
    "dbname": "ecommerce_db",
    "user": "ecommerce_user",
}

PRODUCT_COLUMNS = [
    "product_id",
    "product_category_name",
    "product_name_lenght",
    "product_description_lenght",
    "product_photos_qty",
    "product_weight_g",
    "product_length_cm",
    "product_height_cm",
    "product_width_cm",
]

CATEGORY_COLUMNS = [
    "product_category_name",
    "product_category_name_english",
]


def read_csv_rows(path: Path, expected_columns: list[str]) -> list[list[str]]:
    """Read CSV data and validate its column structure."""
    if not path.is_file():
        raise FileNotFoundError(f"Missing CSV file: {path}")

    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.reader(source)
        header = next(reader, None)

        if header != expected_columns:
            raise ValueError(f"Unexpected columns in {path.name}: {header}")

        rows = list(reader)

    if not rows:
        raise ValueError(f"CSV file is empty: {path.name}")

    for row_number, row in enumerate(rows, start=2):
        if len(row) != len(expected_columns):
            raise ValueError(f"Invalid column count at {path.name}:{row_number}")

    return rows


def validate_references(
    products: list[list[str]],
    categories: list[list[str]],
) -> None:
    """Validate primary keys and product category references."""
    product_ids = [row[0] for row in products]
    category_names = [row[0] for row in categories]

    if any(not product_id for product_id in product_ids):
        raise ValueError("Product IDs cannot be empty.")

    if len(product_ids) != len(set(product_ids)):
        raise ValueError("Duplicate product IDs detected.")

    if len(category_names) != len(set(category_names)):
        raise ValueError("Duplicate category names detected.")

    print("Product IDs: unique")
    print("Category translation keys: unique")

    referenced_categories = {row[1] for row in products if row[1]}

    untranslated = referenced_categories - set(category_names)

    print(f"Categories without translation: {len(untranslated)}")


def prepare_products(rows: list[list[str]]) -> list[tuple]:
    """Convert source CSV fields into database-ready values."""
    prepared = []

    for row in rows:
        values = [value if value != "" else None for value in row]
        prepared.append(tuple(values))

    return prepared


def main() -> None:
    """Validate CSV sources and load product tables transactionally."""
    print("Validating source files...")

    products = read_csv_rows(PRODUCTS_CSV, PRODUCT_COLUMNS)
    categories = read_csv_rows(CATEGORIES_CSV, CATEGORY_COLUMNS)

    validate_references(products, categories)

    print(f"Products in CSV: {len(products):,}")
    print(f"Categories in CSV: {len(categories):,}")

    password = getpass.getpass("PostgreSQL password: ")

    with (
        psycopg.connect(**DB_CONFIG, password=password) as conn,
        conn.cursor() as cursor,
    ):
        cursor.execute("SELECT COUNT(*) FROM products")
        existing_products = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM product_categories")
        existing_categories = cursor.fetchone()[0]

        if existing_products or existing_categories:
            if existing_products == len(products) and existing_categories == len(
                categories
            ):
                print("Expected row counts already exist. No changes made.")
                return

            raise RuntimeError(
                "Product tables already contain data with unexpected "
                "row counts. No changes were made."
            )

        print("Loading product category translations...")

        cursor.executemany(
            """
            INSERT INTO product_categories (
                product_category_name,
                product_category_name_english
            )
            VALUES (%s, %s)
            """,
            [(row[0], row[1]) for row in categories],
        )

        print("Loading products...")

        cursor.executemany(
            """
            INSERT INTO products (
                product_id,
                product_category_name,
                product_name_length,
                product_description_length,
                product_photos_qty,
                product_weight_g,
                product_length_cm,
                product_height_cm,
                product_width_cm
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s
            )
            """,
            prepare_products(products),
        )

        cursor.execute("SELECT COUNT(*) FROM products")
        loaded_products = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM product_categories")
        loaded_categories = cursor.fetchone()[0]

        if loaded_products != len(products) or loaded_categories != len(categories):
            raise RuntimeError("Post-load row count verification failed.")

    print("\nProduct data loaded successfully!")
    print(f"Products: {loaded_products:,}")
    print(f"Category translations: {loaded_categories:,}")


if __name__ == "__main__":
    main()
