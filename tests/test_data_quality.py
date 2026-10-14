
from pathlib import Path

import pandas as pd
import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "raw"


@pytest.fixture(scope="module")
def datasets():
    """Load datasets once for this test module."""
    return {
        "orders": pd.read_csv(
            DATA_DIR / "olist_orders_dataset.csv"
        ),
        "customers": pd.read_csv(
            DATA_DIR / "olist_customers_dataset.csv"
        ),
        "items": pd.read_csv(
            DATA_DIR / "olist_order_items_dataset.csv"
        ),
    }


def test_order_ids_are_unique(datasets):
    orders = datasets["orders"]

    assert orders["order_id"].is_unique, (
        "Duplicate order IDs detected."
    )


def test_orders_reference_existing_customers(datasets):
    orders = datasets["orders"]
    customers = datasets["customers"]

    invalid_references = ~orders["customer_id"].isin(
        customers["customer_id"]
    )

    assert not invalid_references.any(), (
        "Orders reference customers that do not exist."
    )


def test_item_prices_are_positive(datasets):
    items = datasets["items"]

    assert items["price"].notna().all(), (
        "Missing item prices detected."
    )

    assert items["price"].gt(0).all(), (
        "Non-positive item prices detected."
    )
