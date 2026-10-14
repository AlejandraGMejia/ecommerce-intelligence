from pathlib import Path

import pandas as pd

# Find the project folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "raw"

# Tables we will explore first
TABLES = {
    "orders": "olist_orders_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
}


def explore_table(name: str, filename: str) -> None:
    """Display basic information about a CSV dataset."""
    file_path = DATA_DIR / filename

    if not file_path.is_file():
        print(f"File not found: {file_path}")
        return

    df = pd.read_csv(file_path)

    print(f"\n{'=' * 55}")
    print(f"TABLE: {name.upper()}")
    print(f"{'=' * 55}")

    print(f"Rows: {df.shape[0]:,}")
    print(f"Columns: {df.shape[1]}")

    print("\nColumn names and data types:")
    print(df.dtypes.to_string())

    print("\nMissing values:")
    print(df.isna().sum().to_string())

    print("\nFirst 5 rows:")
    print(df.head().to_string(index=False))


def main() -> None:
    for name, filename in TABLES.items():
        explore_table(name, filename)


if __name__ == "__main__":
    main()
