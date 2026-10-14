
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
        ],
    )

    # Rule 1: delivery before carrier handoff
    carrier_anomalies = orders.loc[
        orders["order_delivered_customer_date"].notna()
        & orders["order_delivered_carrier_date"].notna()
        & (
            orders["order_delivered_customer_date"]
            < orders["order_delivered_carrier_date"]
        )
    ].copy()

    carrier_anomalies["time_difference_hours"] = (
        (
            carrier_anomalies["order_delivered_carrier_date"]
            - carrier_anomalies["order_delivered_customer_date"]
        ).dt.total_seconds()
        / 3600
    )

    print("\n=== CARRIER DATE ANOMALIES ===")
    print("Total:", len(carrier_anomalies))

    print(
        carrier_anomalies[
            [
                "order_id",
                "order_status",
                "order_delivered_carrier_date",
                "order_delivered_customer_date",
                "time_difference_hours",
            ]
        ]
        .sort_values("time_difference_hours", ascending=False)
        .head(10)
        .to_string(index=False)
    )

    print("\n=== DIFFERENCE IN HOURS ===")
    print(carrier_anomalies["time_difference_hours"].describe())

    # Rule 2: delivered without delivery date
    missing_delivery = orders.loc[
        orders["order_status"].eq("delivered")
        & orders["order_delivered_customer_date"].isna()
    ].copy()

    print("\n=== DELIVERED WITHOUT DATE ===")
    print("Total:", len(missing_delivery))

    print(
        missing_delivery[
            [
                "order_id",
                "order_purchase_timestamp",
                "order_approved_at",
                "order_delivered_carrier_date",
                "order_delivered_customer_date",
            ]
        ].to_string(index=False)
    )

    overlapping_orders = set(carrier_anomalies["order_id"]) & set(
        missing_delivery["order_id"]
    )

    print("\n=== OVERLAPPING ORDERS ===")
    print("Orders affected by both rules:", len(overlapping_orders))


if __name__ == "__main__":
    main()
