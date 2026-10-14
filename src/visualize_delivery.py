"""Visualize monthly delivery performance from PostgreSQL."""

import getpass
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import psycopg
from matplotlib.ticker import FuncFormatter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"

DB_CONFIG = {
    "host": "localhost",
    "dbname": "ecommerce_db",
    "user": "ecommerce_user",
}

QUERY = """
WITH valid_deliveries AS (
    SELECT
        DATE_TRUNC(
            'month',
            order_purchase_timestamp
        )::DATE AS purchase_month,
        order_delivered_customer_date::DATE AS actual_date,
        order_estimated_delivery_date::DATE AS estimated_date
    FROM orders
    WHERE order_status = 'delivered'
      AND order_purchase_timestamp >= DATE '2017-01-01'
      AND order_purchase_timestamp < DATE '2018-09-01'
      AND order_delivered_customer_date IS NOT NULL
      AND order_estimated_delivery_date IS NOT NULL
      AND order_delivered_customer_date >= order_purchase_timestamp
      AND (
          order_delivered_carrier_date IS NULL
          OR order_delivered_customer_date >= order_delivered_carrier_date
      )
)
SELECT
    purchase_month,
    COUNT(*) AS valid_orders,
    COUNT(*) FILTER (
        WHERE actual_date > estimated_date
    ) AS late_orders,
    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE actual_date > estimated_date
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS late_rate_pct
FROM valid_deliveries
GROUP BY purchase_month
ORDER BY purchase_month;
"""


def fetch_delivery_data(password: str) -> pd.DataFrame:
    """Retrieve monthly late-delivery metrics."""
    with (
        psycopg.connect(**DB_CONFIG, password=password) as conn,
        conn.cursor() as cursor,
    ):
        cursor.execute(QUERY)
        rows = cursor.fetchall()
        columns = [column.name for column in cursor.description]

    return pd.DataFrame(rows, columns=columns)


def format_percent(value: float, _position: int) -> str:
    """Format percentage axis labels."""
    return f"{value:.0f}%"


def create_delivery_chart(data: pd.DataFrame) -> Path:
    """Create an executive monthly late-delivery chart."""
    if data.empty:
        raise ValueError("Cannot visualize an empty dataset.")

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    chart_data = data.copy()
    chart_data["purchase_month"] = pd.to_datetime(chart_data["purchase_month"])
    chart_data["late_rate_pct"] = chart_data["late_rate_pct"].astype(float)
    chart_data = chart_data.sort_values("purchase_month")

    if (chart_data["valid_orders"] <= 0).any():
        raise ValueError("Monthly order counts must be positive.")

    peak_row = chart_data.loc[chart_data["late_rate_pct"].idxmax()]

    fig, ax = plt.subplots(figsize=(13, 7))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    ax.plot(
        chart_data["purchase_month"],
        chart_data["late_rate_pct"],
        color="#2563A6",
        linewidth=2.5,
        marker="o",
        markersize=5,
    )

    ax.scatter(
        peak_row["purchase_month"],
        peak_row["late_rate_pct"],
        color="#D97736",
        s=110,
        zorder=5,
    )

    ax.annotate(
        (
            f"Highest late rate: {peak_row['purchase_month']:%b %Y}\n"
            f"{peak_row['late_rate_pct']:.2f}% "
            f"({peak_row['late_orders']:,} late orders)"
        ),
        xy=(
            peak_row["purchase_month"],
            peak_row["late_rate_pct"],
        ),
        xytext=(-18, 38),
        textcoords="offset points",
        ha="right",
        fontsize=10,
        fontweight="bold",
        color="#333333",
        arrowprops={
            "arrowstyle": "->",
            "color": "#D97736",
            "linewidth": 1.5,
        },
        bbox={
            "boxstyle": "round,pad=0.5",
            "facecolor": "#FFF7ED",
            "edgecolor": "#FED7AA",
        },
    )

    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.yaxis.set_major_formatter(FuncFormatter(format_percent))

    ax.set_ylim(bottom=0, top=max(22, chart_data["late_rate_pct"].max() * 1.2))
    ax.set_xlabel("Purchase Month", fontsize=11, labelpad=12)
    ax.set_ylabel("Late Delivery Rate", fontsize=11)

    ax.grid(axis="y", linestyle="--", alpha=0.2)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.setp(ax.get_xticklabels(), rotation=40, ha="right")

    fig.suptitle(
        "Monthly Late Delivery Rate",
        fontsize=20,
        fontweight="bold",
        x=0.12,
        y=0.97,
        ha="left",
    )

    fig.text(
        0.12,
        0.91,
        "Delivered orders | January 2017 - August 2018",
        fontsize=11,
        color="#555555",
    )

    fig.text(
        0.12,
        0.025,
        (
            "Source: Olist Brazilian E-Commerce Dataset | "
            "Late = actual delivery date after estimated date. "
            "Invalid delivery records excluded."
        ),
        fontsize=9,
        color="#666666",
    )

    fig.subplots_adjust(
        left=0.12,
        right=0.96,
        top=0.83,
        bottom=0.22,
    )

    output_path = FIGURES_DIR / "monthly_delivery_performance.png"

    fig.savefig(
        output_path,
        dpi=200,
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(fig)

    return output_path


def main() -> None:
    """Retrieve delivery data and generate the visualization."""
    password = getpass.getpass("PostgreSQL password: ")
    data = fetch_delivery_data(password)

    if data.empty:
        raise RuntimeError("No monthly delivery records were returned.")

    total_orders = int(data["valid_orders"].sum())
    total_late = int(data["late_orders"].sum())

    if total_orders != 96184 or total_late != 6531:
        raise RuntimeError(
            "Monthly totals do not match the verified baseline: "
            f"{total_orders:,} orders, {total_late:,} late."
        )

    output_path = create_delivery_chart(data)

    print("\nDelivery chart created successfully!")
    print(f"Output: {output_path}")
    print(f"Months analyzed: {len(data)}")
    print(f"Valid orders: {total_orders:,}")
    print(f"Late orders: {total_late:,}")


if __name__ == "__main__":
    main()
