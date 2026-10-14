"""Visualize customer satisfaction by delivery punctuality."""

import getpass
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import psycopg

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
        order_id,
        CASE
            WHEN order_delivered_customer_date::DATE
                 > order_estimated_delivery_date::DATE
            THEN 'Late'
            ELSE 'On Time'
        END AS delivery_status
    FROM orders
    WHERE order_status = 'delivered'
      AND order_purchase_timestamp IS NOT NULL
      AND order_delivered_customer_date IS NOT NULL
      AND order_estimated_delivery_date IS NOT NULL
      AND order_delivered_customer_date >= order_purchase_timestamp
      AND (
          order_delivered_carrier_date IS NULL
          OR order_delivered_customer_date >= order_delivered_carrier_date
      )
),
reviews_per_order AS (
    SELECT
        order_id,
        AVG(review_score::NUMERIC) AS avg_review_score
    FROM reviews
    GROUP BY order_id
),
combined AS (
    SELECT
        d.delivery_status,
        r.avg_review_score
    FROM valid_deliveries AS d
    INNER JOIN reviews_per_order AS r
        ON d.order_id = r.order_id
)
SELECT
    delivery_status,
    COUNT(*) AS reviewed_orders,
    ROUND(
        AVG(avg_review_score),
        2
    ) AS avg_review_score,
    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE avg_review_score <= 2
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS low_rating_rate_pct
FROM combined
GROUP BY delivery_status
ORDER BY
    CASE delivery_status
        WHEN 'On Time' THEN 1
        ELSE 2
    END;
"""


def fetch_satisfaction_data(password: str) -> pd.DataFrame:
    """Retrieve satisfaction metrics from PostgreSQL."""
    with (
        psycopg.connect(**DB_CONFIG, password=password) as conn,
        conn.cursor() as cursor,
    ):
        cursor.execute(QUERY)
        rows = cursor.fetchall()
        columns = [column.name for column in cursor.description]

    return pd.DataFrame(rows, columns=columns)


def create_satisfaction_chart(data: pd.DataFrame) -> Path:
    """Create an executive comparison of low-rating rates."""
    required_statuses = {"On Time", "Late"}

    if set(data["delivery_status"]) != required_statuses:
        raise ValueError("Expected exactly On Time and Late delivery groups.")

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    chart_data = data.copy()

    chart_data["low_rating_rate_pct"] = chart_data["low_rating_rate_pct"].astype(float)

    chart_data["avg_review_score"] = chart_data["avg_review_score"].astype(float)

    chart_data = chart_data.set_index("delivery_status").loc[["On Time", "Late"]]

    labels = ["On-Time Deliveries", "Late Deliveries"]
    values = chart_data["low_rating_rate_pct"].tolist()
    colors = ["#2563A6", "#D97736"]

    # --------------------------------------------------------
    # FIGURE
    # --------------------------------------------------------

    fig, ax = plt.subplots(figsize=(12, 6.5))

    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    y_positions = [0, 1]

    bars = ax.barh(
        y_positions,
        values,
        color=colors,
        height=0.42,
    )

    ax.set_yticks(y_positions, labels)

    # On-time deliveries appear above late deliveries.
    # Extra vertical space keeps descriptions away from the x-axis.
    ax.set_ylim(1.65, -0.65)

    ax.set_xlim(0, 75)

    # --------------------------------------------------------
    # BAR VALUES
    # --------------------------------------------------------

    ax.bar_label(
        bars,
        labels=[f"{value:.2f}%" for value in values],
        padding=10,
        fontsize=13,
        fontweight="bold",
    )

    # --------------------------------------------------------
    # ORDER COUNTS AND AVERAGE RATINGS
    # --------------------------------------------------------

    for index, (_, row) in enumerate(chart_data.iterrows()):
        description = (
            f"{int(row['reviewed_orders']):,} reviewed orders"
            f"  |  Mean rating: {row['avg_review_score']:.2f}/5"
        )

        ax.text(
            0.5,
            index + 0.32,
            description,
            fontsize=10,
            color="#666666",
            ha="left",
            va="center",
        )

    # --------------------------------------------------------
    # AXIS STYLING
    # --------------------------------------------------------

    ax.set_xlabel(
        "Orders With Low Average Review Score (%)",
        fontsize=11,
        labelpad=12,
    )
    ax.set_ylabel("")

    ax.grid(
        axis="x",
        linestyle="--",
        alpha=0.15,
    )
    ax.set_axisbelow(True)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)

    ax.tick_params(axis="both", labelsize=10)

    # --------------------------------------------------------
    # TITLES
    # --------------------------------------------------------

    fig.suptitle(
        "Late Deliveries and Customer Dissatisfaction",
        fontsize=19,
        fontweight="bold",
        x=0.10,
        y=0.96,
        ha="left",
    )

    fig.text(
        0.10,
        0.89,
        ("Share of reviewed orders with an average rating of 2 stars or less"),
        fontsize=11,
        color="#555555",
    )

    # --------------------------------------------------------
    # SOURCE AND METHODOLOGY
    # --------------------------------------------------------

    fig.text(
        0.10,
        0.025,
        (
            "Source: Olist Brazilian E-Commerce Dataset | "
            "One averaged score per order. "
            "Association does not establish causation."
        ),
        fontsize=9,
        color="#666666",
    )

    fig.subplots_adjust(
        left=0.27,
        right=0.92,
        top=0.78,
        bottom=0.20,
    )

    # --------------------------------------------------------
    # EXPORT
    # --------------------------------------------------------

    output_path = FIGURES_DIR / "delivery_vs_satisfaction.png"

    fig.savefig(
        output_path,
        dpi=200,
        bbox_inches="tight",
        facecolor="white",
    )

    plt.close(fig)

    return output_path


def main() -> None:
    """Fetch metrics and generate the satisfaction chart."""
    password = getpass.getpass("PostgreSQL password: ")

    data = fetch_satisfaction_data(password)

    output_path = create_satisfaction_chart(data)

    print("\nSatisfaction chart created successfully!")
    print(f"Output: {output_path}")
    print(f"Delivery groups: {len(data)}")


if __name__ == "__main__":
    main()
