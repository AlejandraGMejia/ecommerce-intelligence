"""Unit tests for monthly customer cohort retention."""

import numpy as np
import pandas as pd
import pytest

from src.visualize_cohorts import (
    FIRST_COHORT,
    LAST_MONTH,
    build_retention_matrix,
)


def make_valid_cohort_data() -> pd.DataFrame:
    """Create a complete synthetic set of monthly cohorts."""
    cohort_months = pd.date_range(
        FIRST_COHORT,
        LAST_MONTH,
        freq="MS",
    )

    records = []

    for cohort_month in cohort_months:
        records.append(
            {
                "cohort_month": cohort_month,
                "cohort_size": 100,
                "cohort_age_months": 0,
                "active_buyers": 100,
                "retention_rate_pct": 100.0,
            }
        )

    records.extend(
        [
            {
                "cohort_month": pd.Timestamp("2017-01-01"),
                "cohort_size": 100,
                "cohort_age_months": 1,
                "active_buyers": 5,
                "retention_rate_pct": 5.0,
            },
            {
                "cohort_month": pd.Timestamp("2017-02-01"),
                "cohort_size": 100,
                "cohort_age_months": 2,
                "active_buyers": 2,
                "retention_rate_pct": 2.0,
            },
        ]
    )

    return pd.DataFrame(records)


def test_retention_values() -> None:
    """Preserve valid cohort retention percentages."""
    matrix = build_retention_matrix(make_valid_cohort_data())

    assert matrix.loc[pd.Timestamp("2017-01-01"), 1] == pytest.approx(5.0)

    assert matrix.loc[pd.Timestamp("2017-02-01"), 2] == pytest.approx(2.0)


def test_missing_activity_becomes_zero() -> None:
    """Represent observable months without activity as zero."""
    matrix = build_retention_matrix(make_valid_cohort_data())

    assert matrix.loc[pd.Timestamp("2017-01-01"), 2] == pytest.approx(0.0)


def test_unobservable_months_are_nan() -> None:
    """Preserve future months as unobservable."""
    matrix = build_retention_matrix(make_valid_cohort_data())

    assert np.isnan(matrix.loc[pd.Timestamp("2018-08-01"), 1])


def test_reject_activity_after_observation_window() -> None:
    """Reject activity beyond the final observation month."""
    df = make_valid_cohort_data()

    invalid_row = pd.DataFrame(
        [
            {
                "cohort_month": pd.Timestamp("2018-08-01"),
                "cohort_size": 100,
                "cohort_age_months": 1,
                "active_buyers": 2,
                "retention_rate_pct": 2.0,
            }
        ]
    )

    df = pd.concat(
        [df, invalid_row],
        ignore_index=True,
    )

    with pytest.raises(
        ValueError,
        match="observation window",
    ):
        build_retention_matrix(df)


def test_month_zero_is_100_percent() -> None:
    """Require 100% activity at month zero for every cohort."""
    matrix = build_retention_matrix(make_valid_cohort_data())

    assert np.allclose(
        matrix[0].to_numpy(),
        100.0,
    )


def test_reject_missing_initial_cohort() -> None:
    """Reject data missing an initial cohort observation."""
    df = make_valid_cohort_data()

    df = df.loc[df["cohort_month"] != pd.Timestamp("2017-03-01")].copy()

    with pytest.raises(
        ValueError,
        match="100% retention at month zero",
    ):
        build_retention_matrix(df)
