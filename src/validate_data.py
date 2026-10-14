from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "raw"


def main() -> None:
    orders = pd.read_csv(DATA_DIR / "olist_orders_dataset.csv")
    customers = pd.read_csv(DATA_DIR / "olist_customers_dataset.csv")
    items = pd.read_csv(DATA_DIR / "olist_order_items_dataset.csv")

    print("\n=== DUPLICATE KEY CHECKS ===")
    print("Duplicate order IDs:", orders["order_id"].duplicated().sum())
    print("Duplicate customer IDs:", customers["customer_id"].duplicated().sum())

    print(
        "Duplicate order item keys:",
        items.duplicated(subset=["order_id", "order_item_id"]).sum(),
    )

    print("\n=== REFERENTIAL INTEGRITY ===")

    invalid_customers = ~orders["customer_id"].isin(customers["customer_id"])

    invalid_orders = ~items["order_id"].isin(orders["order_id"])

    print("Orders without a valid customer:", invalid_customers.sum())
    print("Items without a valid order:", invalid_orders.sum())

    print("\n=== ORDER STATUS DISTRIBUTION ===")
    print(orders["order_status"].value_counts().to_string())

    print("\n=== MISSING DELIVERY DATES BY STATUS ===")

    missing_delivery = orders[orders["order_delivered_customer_date"].isna()]

    print(missing_delivery["order_status"].value_counts().to_string())


if __name__ == "__main__":
    main()
