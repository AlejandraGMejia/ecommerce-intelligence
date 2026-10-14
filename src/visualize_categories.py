"""Visualize top product categories from delivered Olist orders."""

import getpass
from pathlib import Path

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
SELECT
    COALESCE(
        pc.product_category_name_english,
        p.product_category_name,
        'Uncategorized'
    ) AS category,
    SUM(oi.price) AS item_value_brl
FROM order_items AS oi
INNER JOIN orders AS o
    ON oi.order_id = o.order_id
INNER JOIN products AS p
    ON oi.product_id = p.product_id
LEFT JOIN product_categories AS pc
    ON p.product_category_name = pc.product_category_name
WHERE o.order_status = 'delivered'
GROUP BY
    COALESCE(
        pc.product_category_name_english,
        p.product_category_name,
        'Uncategorized'
    )
ORDER BY item_value_brl DESC, category
LIMIT 10;
"""


def fetch_category_data(password: str) -> pd.DataFrame:
    """Retrieve the ten categories with the highest item values."""
    with (
        psycopg.connect(**DB_CONFIG, password=password) as conn,
        conn.cursor() as cursor,
    ):
        cursor.execute(QUERY)
        rows = cursor.fetchall()
        columns = [column.name for column in cursor.description]

    return pd.DataFrame(rows, columns=columns)


def format_millions(value: float, _position: int) -> str:
    """Format the horizontal axis in millions of BRL."""
    return f"R$ {value:.1f}M"


def create_category_chart(data: pd.DataFrame) -> Path:
    """Generate a polished category performance bar chart."""
    if data.empty:
        raise ValueError("Cannot visualize an empty dataset.")

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    chart_data = data.copy()
    chart_data["item_value_brl"] = chart_data["item_value_brl"].astype(float)
    chart_data["item_value_m_brl"] = chart_data["item_value_brl"] / 1_000_000

    chart_data = chart_data.sort_values("item_value_brl")

    labels = chart_data["category"].str.replace("_", " ", regex=False)
    values = chart_data["item_value_m_brl"]

    colors = [
        "#D97736" if category == "health_beauty" else "#2563A6"
        for category in chart_data["category"]
    ]

    fig, ax = plt.subplots(figsize=(13, 7.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    bars = ax.barh(
        labels,
        values,
        color=colors,
        height=0.65,
    )

    ax.bar_label(
        bars,
        labels=[f"R$ {value:,.0f}K" for value in chart_data["item_value_brl"] / 1000],
        padding=6,
        fontsize=9,
    )

    ax.set_xlim(0, values.max() * 1.23)
    ax.xaxis.set_major_formatter(FuncFormatter(format_millions))

    ax.set_xlabel("Delivered-order item value (BRL)", fontsize=11)
    ax.set_ylabel("")

    ax.grid(axis="x", linestyle="--", alpha=0.15)
    ax.set_axisbelow(True)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)

    fig.suptitle(
        "Top 10 Product Categories",
        fontsize=20,
        fontweight="bold",
        x=0.27,
        y=0.97,
        ha="left",
    )

    fig.text(
        0.27,
        0.91,
        "Ranked by item value from delivered orders | Olist E-Commerce",
        fontsize=11,
        color="#555555",
    )

    fig.text(
        0.27,
        0.025,
        (
            "Source: Olist Brazilian E-Commerce Dataset | "
            "Excludes freight; values are not net revenue or profit."
        ),
        fontsize=9,
        color="#666666",
    )

    fig.subplots_adjust(
        left=0.27,
        right=0.95,
        top=0.84,
        bottom=0.17,
    )

    output_path = FIGURES_DIR / "top_categories.png"

    fig.savefig(
        output_path,
        dpi=200,
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(fig)

    return output_path


def main() -> None:
    """Run category visualization workflow."""
    password = getpass.getpass("PostgreSQL password: ")
    data = fetch_category_data(password)

    if data.empty:
        raise RuntimeError("No category data was returned.")

    output_path = create_category_chart(data)

    print("\nCategory chart created successfully!")
    print(f"Output: {output_path}")
    print(f"Categories displayed: {len(data)}")


if __name__ == "__main__":
    main()
