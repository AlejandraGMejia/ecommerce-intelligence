
"""Visualize the top product categories for the BI reporting period."""

import csv
from decimal import Decimal
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_PATH = (
    PROJECT_ROOT / "data" / "processed" / "bi_category_performance.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT / "reports" / "figures" / "bi_top_product_categories.png"
)

EXPECTED_COLUMNS = {
    "category_rank",
    "category",
    "item_value_brl",
}


def load_categories() -> list[dict]:
    """Read and validate the BI category dataset."""

    with INPUT_PATH.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        if not EXPECTED_COLUMNS.issubset(reader.fieldnames or []):
            raise ValueError("Missing required category columns.")

        rows = list(reader)

    if len(rows) < 10:
        raise ValueError("At least 10 categories are required.")

    categories = []

    for row in rows:
        categories.append(
            {
                "rank": int(row["category_rank"]),
                "category": row["category"],
                "value": Decimal(row["item_value_brl"]),
            }
        )

    categories.sort(key=lambda item: item["rank"])

    if [item["rank"] for item in categories] != list(
        range(1, len(categories) + 1)
    ):
        raise ValueError("Invalid category ranking.")

    if len({item["category"] for item in categories}) != len(categories):
        raise ValueError("Duplicate categories detected.")

    if any(item["value"] < 0 for item in categories):
        raise ValueError("Negative item values detected.")

    return categories


def create_chart(categories: list[dict]) -> None:
    """Create a horizontal bar chart of the 10 leading categories."""

    top_ten = categories[:10]

    labels = [
        item["category"].replace("_", " ").title()
        for item in reversed(top_ten)
    ]
    values = [float(item["value"]) for item in reversed(top_ten)]

    fig, ax = plt.subplots(figsize=(12, 7))

    bars = ax.barh(
        labels,
        values,
        color="#2563EB",
        height=0.65,
    )

    ax.set_title(
        "Top 10 Product Categories by Item Value",
        fontsize=17,
        fontweight="bold",
        loc="left",
        pad=20,
    )

    ax.set_xlabel("Delivered Item Value (BRL)", fontsize=11)
    ax.set_ylabel("")

    ax.xaxis.set_major_formatter(
        FuncFormatter(lambda value, _: f"R$ {value / 1_000_000:.1f}M")
    )

    ax.grid(axis="x", linestyle="--", alpha=0.2)
    ax.set_axisbelow(True)

    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.bar_label(
        bars,
        labels=[f"R$ {value / 1_000_000:.2f}M" for value in values],
        padding=5,
        fontsize=9,
    )

    ax.set_xlim(0, max(values) * 1.23)

    fig.text(
        0.12,
        0.015,
        "Delivered orders | Jan 2017 – Aug 2018 | "
        "Item value excludes freight",
        fontsize=9,
        color="#64748B",
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(OUTPUT_PATH, dpi=180, bbox_inches="tight")

    plt.close(fig)


def main() -> None:
    """Load the validated CSV and generate the visualization."""

    categories = load_categories()
    create_chart(categories)

    print("BI category validation: PASSED")
    print(f"Categories analyzed: {len(categories)}")
    print(f"Top category: {categories[0]['category']}")
    print(f"Chart saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
