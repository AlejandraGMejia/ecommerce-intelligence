from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "raw"


def main() -> None:
    orders = pd.read_csv(
        DATA_DIR / "olist_orders_dataset.csv",
        parse_dates=[
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    )

    items = pd.read_csv(DATA_DIR / "olist_order_items_dataset.csv")

    print("\n=== BUSINESS RULE VALIDATIONS ===")

    # 1. Delivery date earlier than purchase date
    invalid_delivery = orders["order_delivered_customer_date"].notna() & (
        orders["order_delivered_customer_date"] < orders["order_purchase_timestamp"]
    )

    print(
        "Deliveries before purchase:",
        invalid_delivery.sum(),
    )

    # 2. Approval earlier than purchase
    invalid_approval = orders["order_approved_at"].notna() & (
        orders["order_approved_at"] < orders["order_purchase_timestamp"]
    )

    print(
        "Approvals before purchase:",
        invalid_approval.sum(),
    )

    # 3. Delivery earlier than carrier handoff
    invalid_carrier = (
        orders["order_delivered_customer_date"].notna()
        & orders["order_delivered_carrier_date"].notna()
        & (
            orders["order_delivered_customer_date"]
            < orders["order_delivered_carrier_date"]
        )
    )

    print(
        "Deliveries before carrier handoff:",
        invalid_carrier.sum(),
    )

    # 4. Negative or zero item prices
    invalid_prices = items["price"].le(0)

    print("Non-positive item prices:", invalid_prices.sum())

    # 5. Negative freight values
    invalid_freight = items["freight_value"].lt(0)

    print("Negative freight values:", invalid_freight.sum())

    # 6. Delivered orders without delivery timestamp
    missing_delivered = (
        orders["order_status"].eq("delivered")
        & orders["order_delivered_customer_date"].isna()
    )

    print(
        "Delivered orders missing delivery timestamp:",
        missing_delivered.sum(),
    )


if __name__ == "__main__":
    main()
