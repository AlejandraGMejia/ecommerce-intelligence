"""Tests for geographic sales performance validation."""

import pandas as pd
import pytest

from src.visualize_geography import (
    validate_geographic_data,
)


def make_valid_geographic_data() -> pd.DataFrame:
    """Create a synthetic dataset matching expected totals."""
    return pd.DataFrame(
        {
            "customer_state": ["SP", "RJ"] + [f"ST{i:02d}" for i in range(25)],
            "delivered_orders": [96_452, 1] + [1] * 25,
            "total_item_value_brl": [
                13_221_472.11,
                1.0,
            ]
            + [1.0] * 25,
            "avg_order_item_value_brl": [
                13_221_472.11 / 96_452,
                1.0,
            ]
            + [1.0] * 25,
        }
    )


def test_valid_geographic_data(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Accept geographically aggregated data with valid totals."""
    df = make_valid_geographic_data()

    validate_geographic_data(df)

    captured = capsys.readouterr()
    assert "PASSED" in captured.out


def test_reject_duplicate_states() -> None:
    """Reject results containing duplicate states."""
    df = make_valid_geographic_data()
    df.loc[1, "customer_state"] = "SP"

    with pytest.raises(ValueError, match="Duplicate"):
        validate_geographic_data(df)


def test_reject_incorrect_order_total() -> None:
    """Reject results that do not reconcile order counts."""
    df = make_valid_geographic_data()
    df.loc[0, "delivered_orders"] += 1

    with pytest.raises(ValueError, match="reconciliation"):
        validate_geographic_data(df)


def test_reject_incorrect_item_value() -> None:
    """Reject results with inconsistent monetary totals."""
    df = make_valid_geographic_data()
    df.loc[0, "total_item_value_brl"] += 100

    with pytest.raises(ValueError, match="reconciliation"):
        validate_geographic_data(df)
