"""Generate an executive geographic sales performance visualization."""

from getpass import getpass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import psycopg

# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUTPUT_PATH = PROJECT_ROOT / "reports" / "figures" / "geographic_performance.png"

MIN_ORDERS = 500

EXPECTED_ORDERS = 96_478
EXPECTED_ITEMS_VALUE = 13_221_498.11
EXPECTED_STATES = 27

# ============================================================
# SQL QUERY
# ============================================================

QUERY = """
WITH delivered_order_values AS (
    SELECT
        o.order_id,
        c.customer_state,
        SUM(oi.price) AS order_item_value
    FROM orders AS o
    INNER JOIN customers AS c
        ON o.customer_id = c.customer_id
    INNER JOIN order_items AS oi
        ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY
        o.order_id,
        c.customer_state
)

SELECT
    customer_state,
    COUNT(*) AS delivered_orders,
    SUM(order_item_value) AS total_item_value_brl,
    AVG(order_item_value) AS avg_order_item_value_brl
FROM delivered_order_values
GROUP BY customer_state
ORDER BY total_item_value_brl DESC;
"""


# ============================================================
# DATA EXTRACTION
# ============================================================


def load_geographic_data() -> pd.DataFrame:
    """Extract geographic business KPIs from PostgreSQL."""

    password = getpass("PostgreSQL password for ecommerce_user: ")

    with (
        psycopg.connect(
            host="localhost",
            dbname="ecommerce_db",
            user="ecommerce_user",
            password=password,
        ) as conn,
        conn.cursor() as cursor,
    ):
        cursor.execute(QUERY)

        rows = cursor.fetchall()

        columns = [description.name for description in cursor.description]

    df = pd.DataFrame(rows, columns=columns)

    if df.empty:
        raise ValueError("No geographic performance data was returned.")

    numeric_columns = [
        "delivered_orders",
        "total_item_value_brl",
        "avg_order_item_value_brl",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="raise",
        )

    return df


# ============================================================
# DATA VALIDATION
# ============================================================


def validate_geographic_data(df: pd.DataFrame) -> None:
    """Validate geographic metrics against known business KPIs."""

    if len(df) != EXPECTED_STATES:
        raise ValueError(f"Expected {EXPECTED_STATES} states, but received {len(df)}.")

    if df["customer_state"].isna().any():
        raise ValueError("Missing customer state detected.")

    if df["customer_state"].duplicated().any():
        raise ValueError("Duplicate customer states detected.")

    if (
        df[
            [
                "delivered_orders",
                "total_item_value_brl",
                "avg_order_item_value_brl",
            ]
        ]
        .isna()
        .any()
        .any()
    ):
        raise ValueError("Missing geographic KPI values detected.")

    if (df["delivered_orders"] <= 0).any():
        raise ValueError("Invalid delivered-order counts detected.")

    if (df["total_item_value_brl"] <= 0).any():
        raise ValueError("Invalid delivered-item values detected.")

    actual_orders = int(df["delivered_orders"].sum())

    if actual_orders != EXPECTED_ORDERS:
        raise ValueError(
            "Delivered-order reconciliation failed: "
            f"expected {EXPECTED_ORDERS:,}, "
            f"received {actual_orders:,}."
        )

    actual_value = float(df["total_item_value_brl"].sum())

    if abs(actual_value - EXPECTED_ITEMS_VALUE) > 0.01:
        raise ValueError(
            "Monetary reconciliation failed: "
            f"expected R$ {EXPECTED_ITEMS_VALUE:,.2f}, "
            f"received R$ {actual_value:,.2f}."
        )

    print("Geographic KPI reconciliation: PASSED")


# ============================================================
# VISUALIZATION
# ============================================================


def create_visualization(df: pd.DataFrame) -> None:
    """Create a two-panel geographic executive report."""

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(17, 8),
        gridspec_kw={
            "width_ratios": [1.1, 1],
        },
    )

    fig.suptitle(
        "Geographic E-Commerce Performance",
        fontsize=20,
        fontweight="bold",
        x=0.06,
        y=0.97,
        ha="left",
    )

    fig.text(
        0.06,
        0.915,
        ("Brazilian States | Delivered Orders | Item Value Excluding Freight"),
        fontsize=11,
        color="#64748B",
    )

    # --------------------------------------------------------
    # PANEL 1: TOTAL DELIVERED ITEM VALUE
    # --------------------------------------------------------

    top_value = df.nlargest(
        10,
        "total_item_value_brl",
    ).sort_values("total_item_value_brl")

    bar_colors = [
        "#0F766E" if state == "SP" else "#94A3B8"
        for state in top_value["customer_state"]
    ]

    values_millions = top_value["total_item_value_brl"] / 1_000_000

    axes[0].barh(
        top_value["customer_state"],
        values_millions,
        color=bar_colors,
        height=0.65,
    )

    axes[0].set_title(
        "Top 10 States by Item Value",
        loc="left",
        fontsize=14,
        fontweight="bold",
        pad=16,
    )

    axes[0].set_xlabel("Delivered item value (R$ millions)")

    axes[0].grid(
        axis="x",
        alpha=0.15,
    )

    axes[0].set_axisbelow(True)

    max_value = float(values_millions.max())

    axes[0].set_xlim(
        0,
        max_value * 1.3,
    )

    for position, value in enumerate(values_millions):
        axes[0].text(
            value + max_value * 0.02,
            position,
            f"R$ {value:.2f}M",
            va="center",
            fontsize=9,
            fontweight="medium",
        )

    # --------------------------------------------------------
    # PANEL 2: AVERAGE ITEM VALUE PER ORDER
    # --------------------------------------------------------

    eligible_states = df.loc[df["delivered_orders"] >= MIN_ORDERS].copy()

    if eligible_states.empty:
        raise ValueError("No states meet the minimum delivered-order threshold.")

    top_average = eligible_states.nlargest(
        10,
        "avg_order_item_value_brl",
    ).sort_values("avg_order_item_value_brl")

    axes[1].barh(
        top_average["customer_state"],
        top_average["avg_order_item_value_brl"],
        color="#2563A6",
        height=0.65,
    )

    axes[1].set_title(
        "Highest Average Item Value per Order",
        loc="left",
        fontsize=14,
        fontweight="bold",
        pad=16,
    )

    axes[1].set_xlabel("Average item value per order (R$)")

    axes[1].grid(
        axis="x",
        alpha=0.15,
    )

    axes[1].set_axisbelow(True)

    max_average = float(top_average["avg_order_item_value_brl"].max())

    axes[1].set_xlim(
        0,
        max_average * 1.5,
    )

    for position, row in enumerate(top_average.itertuples(index=False)):
        axes[1].text(
            (row.avg_order_item_value_brl + max_average * 0.02),
            position,
            (f"R$ {row.avg_order_item_value_brl:,.2f}  (n={row.delivered_orders:,})"),
            va="center",
            fontsize=8.5,
        )

    # --------------------------------------------------------
    # FOOTNOTES
    # --------------------------------------------------------

    fig.text(
        0.06,
        0.055,
        (
            "Source: Olist Brazilian E-Commerce Dataset | "
            f"Average comparison requires at least "
            f"{MIN_ORDERS:,} delivered orders per state."
        ),
        fontsize=9,
        color="#64748B",
    )

    fig.text(
        0.06,
        0.03,
        (
            "Metrics use customer location and exclude "
            "freight. Item value is not net revenue or profit."
        ),
        fontsize=9,
        color="#64748B",
    )

    plt.subplots_adjust(
        left=0.08,
        right=0.97,
        top=0.84,
        bottom=0.15,
        wspace=0.34,
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
    """Run geographic data extraction and visualization."""

    print("Loading geographic sales performance...")

    df = load_geographic_data()

    validate_geographic_data(df)

    total_orders = int(df["delivered_orders"].sum())

    total_value = float(df["total_item_value_brl"].sum())

    print(f"States analyzed: {len(df)}")

    print(f"Delivered orders: {total_orders:,}")

    print(f"Total delivered item value: R$ {total_value:,.2f}")

    create_visualization(df)


if __name__ == "__main__":
    main()
