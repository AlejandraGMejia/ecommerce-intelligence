"""Create an executive RFM customer segmentation visualization."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "customer_rfm_segments.csv"

OUTPUT_PATH = PROJECT_ROOT / "reports" / "figures" / "customer_rfm_segmentation.png"

EXPECTED_CUSTOMERS = 93_358
EXPECTED_ITEM_VALUE = 13_221_498.11
EXPECTED_SEGMENTS = 7

REQUIRED_COLUMNS = {
    "customer_segment",
    "customers",
    "customer_share_pct",
    "avg_recency_days",
    "avg_frequency",
    "avg_monetary_value_brl",
    "total_item_value_brl",
}

SEGMENT_LABELS = {
    "Inactive One-Time Buyers": "Inactive One-Time",
    "High-Value One-Time Buyers": "High-Value One-Time",
    "Recent One-Time Buyers": "Recent One-Time",
    "Developing One-Time Buyers": "Developing One-Time",
    "At-Risk Repeat Buyers": "At-Risk Repeat",
    "Loyal Customers": "Loyal Customers",
    "Champions": "Champions",
}


# ============================================================
# DATA LOADING
# ============================================================


def load_rfm_data() -> pd.DataFrame:
    """Load RFM segment metrics from the exported CSV."""
    if not INPUT_PATH.is_file():
        raise FileNotFoundError(f"RFM CSV not found: {INPUT_PATH}")

    df = pd.read_csv(INPUT_PATH)

    missing_columns = REQUIRED_COLUMNS - set(df.columns)

    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

    if df.empty:
        raise ValueError("RFM data is empty.")

    numeric_columns = sorted(REQUIRED_COLUMNS - {"customer_segment"})

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="raise",
        )

    return df


# ============================================================
# DATA VALIDATION
# ============================================================


def validate_rfm_data(df: pd.DataFrame) -> None:
    """Validate segment integrity and business KPI reconciliation."""

    if len(df) != EXPECTED_SEGMENTS:
        raise ValueError(f"Expected {EXPECTED_SEGMENTS} segments, received {len(df)}.")

    if df["customer_segment"].isna().any():
        raise ValueError("Missing customer segment detected.")

    if df["customer_segment"].duplicated().any():
        raise ValueError("Duplicate customer segments detected.")

    if set(df["customer_segment"]) != set(SEGMENT_LABELS):
        raise ValueError("Unexpected customer segment names.")

    numeric_columns = [
        "customers",
        "customer_share_pct",
        "avg_recency_days",
        "avg_frequency",
        "avg_monetary_value_brl",
        "total_item_value_brl",
    ]

    if df[numeric_columns].isna().any().any():
        raise ValueError("Missing numeric KPI values detected.")

    if not np.isfinite(df[numeric_columns].to_numpy(dtype=float)).all():
        raise ValueError("Non-finite KPI values detected.")

    if (df["customers"] <= 0).any():
        raise ValueError("Invalid customer counts detected.")

    if (df["customers"] % 1 != 0).any():
        raise ValueError("Customer counts must be integers.")

    if ((df["customer_share_pct"] < 0) | (df["customer_share_pct"] > 100)).any():
        raise ValueError("Invalid customer percentages detected.")

    if (df["total_item_value_brl"] < 0).any():
        raise ValueError("Negative monetary values detected.")

    actual_customers = int(df["customers"].sum())

    if actual_customers != EXPECTED_CUSTOMERS:
        raise ValueError(
            "Customer reconciliation failed: "
            f"expected {EXPECTED_CUSTOMERS:,}, "
            f"received {actual_customers:,}."
        )

    actual_value = float(df["total_item_value_brl"].sum())

    if abs(actual_value - EXPECTED_ITEM_VALUE) > 0.01:
        raise ValueError(
            "Monetary reconciliation failed: "
            f"expected R$ {EXPECTED_ITEM_VALUE:,.2f}, "
            f"received R$ {actual_value:,.2f}."
        )

    calculated_shares = 100.0 * df["customers"] / EXPECTED_CUSTOMERS

    if not np.allclose(
        calculated_shares,
        df["customer_share_pct"],
        atol=0.011,
    ):
        raise ValueError("Customer segment percentages do not reconcile.")

    if not np.isclose(
        calculated_shares.sum(),
        100.0,
        atol=0.001,
    ):
        raise ValueError("Customer percentages do not total 100%.")

    print("RFM KPI reconciliation: PASSED")


# ============================================================
# VISUALIZATION
# ============================================================


def create_visualization(df: pd.DataFrame) -> None:
    """Compare customer share and delivered item-value share."""

    plot_data = df.copy()

    plot_data["value_share_pct"] = (
        100.0 * plot_data["total_item_value_brl"] / EXPECTED_ITEM_VALUE
    )

    plot_data["display_label"] = plot_data["customer_segment"].map(SEGMENT_LABELS)

    plot_data = plot_data.sort_values(
        "total_item_value_brl",
        ascending=True,
    )

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )

    fig, ax = plt.subplots(figsize=(15, 9))

    positions = np.arange(len(plot_data))
    bar_height = 0.34

    ax.barh(
        positions - bar_height / 2,
        plot_data["customer_share_pct"],
        height=bar_height,
        color="#94A3B8",
        label="Share of Customers",
    )

    ax.barh(
        positions + bar_height / 2,
        plot_data["value_share_pct"],
        height=bar_height,
        color="#0F766E",
        label="Share of Item Value",
    )

    ax.set_yticks(positions)
    ax.set_yticklabels(
        plot_data["display_label"],
        fontsize=10,
    )

    ax.set_xlabel(
        "Share of Total (%)",
        fontsize=11,
        labelpad=12,
    )

    ax.set_title(
        "Customer Segmentation: RFM Analysis",
        loc="left",
        fontsize=20,
        fontweight="bold",
        pad=32,
    )

    ax.grid(
        axis="x",
        alpha=0.15,
    )
    ax.set_axisbelow(True)

    max_share = float(
        max(
            plot_data["customer_share_pct"].max(),
            plot_data["value_share_pct"].max(),
        )
    )

    ax.set_xlim(
        0,
        max_share * 1.22,
    )

    for position, row in enumerate(plot_data.itertuples(index=False)):
        ax.text(
            row.customer_share_pct + 0.5,
            position - bar_height / 2,
            f"{row.customer_share_pct:.2f}%",
            va="center",
            fontsize=9,
            color="#475569",
        )

        ax.text(
            row.value_share_pct + 0.5,
            position + bar_height / 2,
            f"{row.value_share_pct:.2f}%",
            va="center",
            fontsize=9,
            color="#0F766E",
            fontweight="bold",
        )

    ax.legend(
        loc="lower right",
        frameon=False,
        fontsize=10,
    )

    fig.subplots_adjust(
        left=0.22,
        right=0.96,
        top=0.86,
        bottom=0.20,
    )

    fig.text(
        0.22,
        0.105,
        "Reference date: September 1, 2018 | 93,358 buyers | 7 exclusive segments",
        fontsize=10,
        color="#475569",
    )

    fig.text(
        0.22,
        0.075,
        "Source: Olist Brazilian E-Commerce Dataset | Delivered orders only",
        fontsize=9,
        color="#64748B",
    )

    fig.text(
        0.22,
        0.050,
        "Item value excludes freight and is not net revenue or profit.",
        fontsize=9,
        color="#64748B",
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig.savefig(
        OUTPUT_PATH,
        dpi=220,
        bbox_inches="tight",
        facecolor="white",
    )

    plt.close(fig)

    print(f"Visualization saved: {OUTPUT_PATH}")


# ============================================================
# MAIN
# ============================================================


def main() -> None:
    """Validate and visualize RFM customer segments."""

    print("Loading customer RFM segmentation data...")

    df = load_rfm_data()

    validate_rfm_data(df)

    print(f"Segments analyzed: {len(df)}")
    print(f"Total buyers: {int(df['customers'].sum()):,}")
    print(f"Total delivered item value: R$ {df['total_item_value_brl'].sum():,.2f}")

    create_visualization(df)


if __name__ == "__main__":
    main()
