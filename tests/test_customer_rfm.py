"""Automated tests for RFM customer segmentation validation."""

import pandas as pd
import pytest

from src.visualize_rfm import (
    EXPECTED_CUSTOMERS,
    EXPECTED_ITEM_VALUE,
    validate_rfm_data,
)


@pytest.fixture
def valid_rfm_data():
    """Build a valid synthetic RFM segmentation dataset."""

    segments = [
        ("Inactive One-Time Buyers", 49839, 339.31, 1.00),
        ("High-Value One-Time Buyers", 5970, 291.13, 1.00),
        ("Recent One-Time Buyers", 17469, 46.43, 1.00),
        ("Developing One-Time Buyers", 17279, 136.97, 1.00),
        ("At-Risk Repeat Buyers", 1587, 322.85, 2.08),
        ("Loyal Customers", 834, 112.18, 2.12),
        ("Champions", 380, 47.80, 2.23),
    ]

    item_values = [
        4672548.46,
        3758828.66,
        2401887.46,
        1659824.78,
        400590.59,
        187221.30,
        140596.86,
    ]

    records = []

    for (name, customers, recency, frequency), value in zip(
        segments,
        item_values,
        strict=True,
    ):
        records.append(
            {
                "customer_segment": name,
                "customers": customers,
                "customer_share_pct": round(
                    100 * customers / EXPECTED_CUSTOMERS,
                    2,
                ),
                "avg_recency_days": recency,
                "avg_frequency": frequency,
                "avg_monetary_value_brl": round(
                    value / customers,
                    2,
                ),
                "total_item_value_brl": value,
            }
        )

    return pd.DataFrame(records)


def test_valid_rfm_data_passes(valid_rfm_data):
    """Valid RFM data must pass reconciliation."""

    validate_rfm_data(valid_rfm_data)


def test_customer_totals_reconcile(valid_rfm_data):
    """Customer counts must match the expected population."""

    assert valid_rfm_data["customers"].sum() == EXPECTED_CUSTOMERS


def test_monetary_totals_reconcile(valid_rfm_data):
    """Monetary totals must match delivered-order item value."""

    assert (
        abs(valid_rfm_data["total_item_value_brl"].sum() - EXPECTED_ITEM_VALUE) <= 0.01
    )


def test_duplicate_segments_are_rejected(valid_rfm_data):
    """Duplicate segment names must fail validation."""

    invalid = valid_rfm_data.copy()

    invalid.loc[1, "customer_segment"] = invalid.loc[
        0,
        "customer_segment",
    ]

    with pytest.raises(ValueError, match="Duplicate"):
        validate_rfm_data(invalid)


def test_incorrect_customer_total_is_rejected(valid_rfm_data):
    """Incorrect customer counts must fail reconciliation."""

    invalid = valid_rfm_data.copy()

    invalid.loc[0, "customers"] += 10

    with pytest.raises(ValueError, match="Customer reconciliation"):
        validate_rfm_data(invalid)


def test_incorrect_monetary_total_is_rejected(valid_rfm_data):
    """Incorrect monetary values must fail reconciliation."""

    invalid = valid_rfm_data.copy()

    invalid.loc[0, "total_item_value_brl"] += 100

    with pytest.raises(ValueError, match="Monetary reconciliation"):
        validate_rfm_data(invalid)


def test_incorrect_customer_share_is_rejected(valid_rfm_data):
    """Incorrect segment percentages must fail validation."""

    invalid = valid_rfm_data.copy()

    invalid.loc[0, "customer_share_pct"] = 10.0

    with pytest.raises(ValueError, match="percentages"):
        validate_rfm_data(invalid)


def test_negative_customer_count_is_rejected(valid_rfm_data):
    """Customer counts cannot be negative."""

    invalid = valid_rfm_data.copy()

    invalid.loc[0, "customers"] = -1

    with pytest.raises(ValueError, match="Invalid customer counts"):
        validate_rfm_data(invalid)


def test_missing_segment_is_rejected(valid_rfm_data):
    """All seven expected segments must be present."""

    invalid = valid_rfm_data.iloc[:-1].copy()

    with pytest.raises(ValueError, match="Expected 7 segments"):
        validate_rfm_data(invalid)
