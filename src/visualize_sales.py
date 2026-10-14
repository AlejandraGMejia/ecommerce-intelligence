"""Generate an executive sales visualization using PostgreSQL data."""

import getpass
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import psycopg
from matplotlib.ticker import FuncFormatter

# ------------------------------------------------------------
# PROJECT CONFIGURATION
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports" / "figures"

DB_CONFIG = {
    "host": "localhost",
    "dbname": "ecommerce_db",
    "user": "ecommerce_user",
}

# ------------------------------------------------------------
# SQL QUERY
# ------------------------------------------------------------

QUERY = """
WITH order_values AS (
    SELECT
        o.order_id,
        DATE_TRUNC(
            'month',
            o.order_purchase_timestamp
        )::DATE AS purchase_month,
        SUM(oi.price) AS item_value
    FROM orders AS o
    INNER JOIN order_items AS oi
        ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY
        o.order_id,
        DATE_TRUNC(
            'month',
            o.order_purchase_timestamp
        )::DATE
)
SELECT
    purchase_month,
    SUM(item_value) AS item_value_brl
FROM order_values
WHERE purchase_month >= DATE '2017-01-01'
  AND purchase_month < DATE '2018-09-01'
GROUP BY purchase_month
ORDER BY purchase_month;
"""


def format_brl_thousands(value: float, _position: int) -> str:
    """Format monetary values in thousands of BRL."""
    return f"R$ {value:,.0f}K"


def fetch_monthly_sales(password: str) -> pd.DataFrame:
    """Retrieve monthly delivered-order item values."""
    with (
        psycopg.connect(**DB_CONFIG, password=password) as conn,
        conn.cursor() as cursor,
    ):
        cursor.execute(QUERY)
        rows = cursor.fetchall()
        columns = [column.name for column in cursor.description]

    return pd.DataFrame(rows, columns=columns)


def create_sales_chart(data: pd.DataFrame) -> Path:
    """Generate and save an executive monthly performance chart."""
    if data.empty:
        raise ValueError("Cannot visualize an empty dataset.")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    chart_data = data.copy()

    chart_data["purchase_month"] = pd.to_datetime(chart_data["purchase_month"])
    chart_data["item_value_brl"] = chart_data["item_value_brl"].astype(float)

    chart_data = chart_data.sort_values("purchase_month")

    chart_data["item_value_k_brl"] = chart_data["item_value_brl"] / 1000

    peak_row = chart_data.loc[chart_data["item_value_brl"].idxmax()]

    # --------------------------------------------------------
    # VISUAL DESIGN
    # --------------------------------------------------------

    fig, ax = plt.subplots(figsize=(13, 7))

    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    ax.plot(
        chart_data["purchase_month"],
        chart_data["item_value_k_brl"],
        color="#2563A6",
        marker="o",
        markersize=6,
        linewidth=2.5,
    )

    ax.scatter(
        peak_row["purchase_month"],
        peak_row["item_value_k_brl"],
        color="#D97736",
        s=100,
        zorder=5,
    )

    # --------------------------------------------------------
    # TITLE AND SUBTITLE
    # --------------------------------------------------------

    fig.suptitle(
        "Monthly E-Commerce Performance",
        fontsize=20,
        fontweight="bold",
        x=0.12,
        y=0.97,
        ha="left",
    )

    fig.text(
        0.12,
        0.91,
        "Delivered-order item value | January 2017 - August 2018",
        fontsize=11,
        color="#555555",
    )

    # --------------------------------------------------------
    # AXES
    # --------------------------------------------------------

    ax.set_xlabel("Purchase Month", fontsize=11, labelpad=12)
    ax.set_ylabel("Item Value (BRL, thousands)", fontsize=11)

    ax.yaxis.set_major_formatter(FuncFormatter(format_brl_thousands))

    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))

    ax.grid(
        axis="y",
        alpha=0.2,
        linestyle="--",
    )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.setp(
        ax.get_xticklabels(),
        rotation=40,
        ha="right",
    )

    # --------------------------------------------------------
    # PEAK MONTH ANNOTATION
    # --------------------------------------------------------

    peak_label = (
        f"Peak: {peak_row['purchase_month']:%b %Y}\n"
        f"R$ {peak_row['item_value_brl']:,.0f}"
    )

    ax.annotate(
        peak_label,
        xy=(
            peak_row["purchase_month"],
            peak_row["item_value_k_brl"],
        ),
        xytext=(24, -65),
        textcoords="offset points",
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

    # --------------------------------------------------------
    # DATA CONTEXT
    # --------------------------------------------------------

    fig.text(
        0.12,
        0.025,
        (
            "Source: Olist Brazilian E-Commerce Dataset | "
            "Historical data | Values exclude freight and "
            "do not represent net revenue or profit."
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

    # --------------------------------------------------------
    # EXPORT
    # --------------------------------------------------------

    output_path = REPORTS_DIR / "monthly_sales_executive.png"

    fig.savefig(
        output_path,
        dpi=200,
        bbox_inches="tight",
        facecolor="white",
    )

    plt.close(fig)

    return output_path


def main() -> None:
    """Execute the visualization workflow."""
    password = getpass.getpass("PostgreSQL password: ")

    data = fetch_monthly_sales(password)

    if data.empty:
        raise RuntimeError("No monthly sales records were returned.")

    output_path = create_sales_chart(data)

    print("\nChart created successfully!")
    print(f"Output: {output_path}")
    print(f"Months analyzed: {len(data)}")


if __name__ == "__main__":
    main()
