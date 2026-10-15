"""Generate and validate a monthly customer cohort retention heatmap."""

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

INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "customer_cohorts.csv"

OUTPUT_PATH = PROJECT_ROOT / "reports" / "figures" / "customer_cohort_retention.png"

FIRST_COHORT = pd.Timestamp("2017-01-01")
LAST_MONTH = pd.Timestamp("2018-08-01")

# Use a narrow scale to distinguish low retention rates.
# Month zero (100%) remains saturated and is labeled explicitly.
COLOR_SCALE_MAX = 1.0


# ============================================================
# DATA LOADING AND VALIDATION
# ============================================================


def load_cohort_data() -> pd.DataFrame:
    """Load and validate cohort retention results exported from SQL."""
    if not INPUT_PATH.is_file():
        raise FileNotFoundError(f"Cohort CSV not found: {INPUT_PATH}")

    df = pd.read_csv(
        INPUT_PATH,
        parse_dates=["cohort_month"],
    )

    required_columns = {
        "cohort_month",
        "cohort_size",
        "cohort_age_months",
        "active_buyers",
        "retention_rate_pct",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(f"Missing columns: {sorted(missing_columns)}")

    if df.empty:
        raise ValueError("The cohort dataset is empty.")

    if df[list(required_columns)].isna().any().any():
        raise ValueError("Missing cohort values detected.")

    if df.duplicated(["cohort_month", "cohort_age_months"]).any():
        raise ValueError("Duplicate cohort-month combinations detected.")

    integer_columns = [
        "cohort_size",
        "cohort_age_months",
        "active_buyers",
    ]

    for column in integer_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="raise",
        )

        if not np.isfinite(df[column]).all():
            raise ValueError(f"Invalid numeric values in {column}.")

        if (df[column] % 1 != 0).any():
            raise ValueError(f"Non-integer values detected in {column}.")

        df[column] = df[column].astype(int)

    df["retention_rate_pct"] = pd.to_numeric(
        df["retention_rate_pct"],
        errors="raise",
    )

    if not np.isfinite(df["retention_rate_pct"]).all():
        raise ValueError("Non-finite retention percentages detected.")

    if (df["cohort_size"] <= 0).any():
        raise ValueError("Invalid cohort sizes detected.")

    if (df["cohort_age_months"] < 0).any():
        raise ValueError("Negative cohort ages detected.")

    if ((df["active_buyers"] < 0) | (df["active_buyers"] > df["cohort_size"])).any():
        raise ValueError("Invalid active buyer counts detected.")

    calculated_rates = 100.0 * df["active_buyers"] / df["cohort_size"]

    if not np.allclose(
        calculated_rates,
        df["retention_rate_pct"],
        atol=0.011,
    ):
        raise ValueError(
            "Retention percentages do not reconcile "
            "with active buyers and cohort sizes."
        )

    print("Cohort data validation: PASSED")

    return df


# ============================================================
# RETENTION MATRIX
# ============================================================


def build_retention_matrix(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Distinguish zero retention from unobservable months."""
    cohort_months = pd.date_range(
        FIRST_COHORT,
        LAST_MONTH,
        freq="MS",
    )

    max_age = (
        (LAST_MONTH.year - FIRST_COHORT.year) * 12
        + LAST_MONTH.month
        - FIRST_COHORT.month
    )

    matrix = pd.DataFrame(
        np.nan,
        index=cohort_months,
        columns=range(max_age + 1),
        dtype=float,
    )

    # Months within the observation period are initially zero.
    # Future/unobservable months remain NaN.
    for cohort_month in cohort_months:
        observable_age = (
            (LAST_MONTH.year - cohort_month.year) * 12
            + LAST_MONTH.month
            - cohort_month.month
        )

        matrix.loc[
            cohort_month,
            0:observable_age,
        ] = 0.0

    # Populate months for which SQL returned actual activity.
    for row in df.itertuples(index=False):
        cohort_month = pd.Timestamp(row.cohort_month)
        cohort_age = int(row.cohort_age_months)

        if cohort_month not in matrix.index:
            raise ValueError(f"Unexpected cohort month: {cohort_month}")

        if cohort_age not in matrix.columns:
            raise ValueError(f"Unexpected cohort age: {cohort_age}")

        if pd.isna(matrix.loc[cohort_month, cohort_age]):
            raise ValueError("Activity detected outside the observation window.")

        matrix.loc[
            cohort_month,
            cohort_age,
        ] = float(row.retention_rate_pct)

    if not np.allclose(
        matrix[0].to_numpy(),
        100.0,
    ):
        raise ValueError("All cohorts must have 100% retention at month zero.")

    print("Retention matrix validation: PASSED")

    return matrix


# ============================================================
# VISUALIZATION
# ============================================================


def create_heatmap(matrix: pd.DataFrame) -> None:
    """Create a presentation-ready cohort retention heatmap."""
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )

    fig, ax = plt.subplots(figsize=(17, 11))

    data = matrix.to_numpy(dtype=float)
    masked_data = np.ma.masked_invalid(data)

    color_map = plt.get_cmap("Blues").copy()
    color_map.set_bad("#F1F5F9")

    image = ax.imshow(
        masked_data,
        aspect="auto",
        interpolation="nearest",
        cmap=color_map,
        vmin=0,
        vmax=COLOR_SCALE_MAX,
    )

    ax.set_title(
        "Monthly Customer Cohort Retention",
        fontsize=20,
        fontweight="bold",
        loc="left",
        pad=25,
    )

    ax.set_xlabel(
        "Months Since First Purchase",
        fontsize=11,
        labelpad=12,
    )

    ax.set_ylabel(
        "First Purchase Month",
        fontsize=11,
        labelpad=12,
    )

    ax.set_xticks(range(len(matrix.columns)))
    ax.set_xticklabels([str(column) for column in matrix.columns])

    ax.set_yticks(range(len(matrix.index)))
    ax.set_yticklabels(matrix.index.strftime("%Y-%m"))

    ax.tick_params(
        axis="both",
        which="major",
        labelsize=9,
    )

    # --------------------------------------------------------
    # CELL LABELS
    # --------------------------------------------------------

    for row_index in range(data.shape[0]):
        for column_index in range(data.shape[1]):
            value = data[row_index, column_index]

            if np.isnan(value):
                continue

            if column_index == 0:
                label = "100%"
            else:
                label = f"{value:.1f}%"

            text_color = "white" if value >= 0.55 else "#0F172A"

            ax.text(
                column_index,
                row_index,
                label,
                ha="center",
                va="center",
                fontsize=7.7,
                color=text_color,
            )

    # --------------------------------------------------------
    # COLOR BAR
    # --------------------------------------------------------

    colorbar = fig.colorbar(
        image,
        ax=ax,
        fraction=0.025,
        pad=0.025,
        extend="max",
    )

    colorbar.set_label(
        "Monthly Retention Rate (%)",
        fontsize=10,
        labelpad=12,
    )

    # --------------------------------------------------------
    # FOOTNOTES
    # --------------------------------------------------------

    fig.subplots_adjust(
        left=0.12,
        right=0.92,
        top=0.88,
        bottom=0.20,
    )

    fig.text(
        0.12,
        0.105,
        ("Month 0 = 100% | Light gray = not observable | 0.0% = no returning buyers"),
        fontsize=10,
        color="#475569",
    )

    fig.text(
        0.12,
        0.078,
        ("Retention = active buyers in a given month / initial cohort size."),
        fontsize=10,
        color="#475569",
    )

    fig.text(
        0.12,
        0.051,
        (
            "Source: Olist Brazilian E-Commerce Dataset | "
            "Delivered orders | Non-cumulative monthly retention"
        ),
        fontsize=9,
        color="#64748B",
    )

    # --------------------------------------------------------
    # SAVE FIGURE
    # --------------------------------------------------------

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

    print(f"Heatmap saved: {OUTPUT_PATH}")


# ============================================================
# MAIN
# ============================================================


def main() -> None:
    """Validate cohort data and generate its heatmap."""
    print("Loading customer cohort data...")

    df = load_cohort_data()
    matrix = build_retention_matrix(df)

    print(f"CSV records: {len(df)}")
    print(f"Cohorts analyzed: {len(matrix)}")
    print(f"Months displayed: {len(matrix.columns)}")

    create_heatmap(matrix)


if __name__ == "__main__":
    main()
