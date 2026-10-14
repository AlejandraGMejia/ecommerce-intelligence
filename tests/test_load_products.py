"""Unit tests for the Olist product data loader."""

import pytest

from src.load_products import (
    prepare_products,
    read_csv_rows,
    validate_references,
)


def test_read_csv_rows(tmp_path):
    """Read a valid CSV file and return its records."""
    csv_file = tmp_path / "products.csv"
    csv_file.write_text(
        "product_id,product_category_name\n"
        "product_1,health_beauty\n"
        "product_2,sports_leisure\n",
        encoding="utf-8",
    )

    rows = read_csv_rows(
        csv_file,
        ["product_id", "product_category_name"],
    )

    assert len(rows) == 2
    assert rows[0] == ["product_1", "health_beauty"]


def test_read_csv_rows_rejects_wrong_header(tmp_path):
    """Reject unexpected CSV columns."""
    csv_file = tmp_path / "products.csv"
    csv_file.write_text(
        "wrong_column,category\nproduct_1,health_beauty\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unexpected columns"):
        read_csv_rows(
            csv_file,
            ["product_id", "product_category_name"],
        )


def test_read_csv_rows_rejects_missing_file(tmp_path):
    """Reject a missing CSV file."""
    missing_file = tmp_path / "missing.csv"

    with pytest.raises(FileNotFoundError):
        read_csv_rows(
            missing_file,
            ["product_id", "product_category_name"],
        )


def test_validate_references_rejects_duplicate_product_ids():
    """Reject duplicate product primary keys."""
    products = [
        ["product_1", "health_beauty"],
        ["product_1", "sports_leisure"],
    ]
    categories = [
        ["health_beauty", "health_beauty"],
        ["sports_leisure", "sports_leisure"],
    ]

    with pytest.raises(ValueError, match="Duplicate product IDs"):
        validate_references(products, categories)


def test_validate_references_preserves_untranslated_categories():
    """Allow original categories without English translations."""
    products = [
        ["product_1", "pc_gamer"],
    ]
    categories = [
        ["health_beauty", "health_beauty"],
    ]

    validate_references(products, categories)


def test_prepare_products_converts_empty_fields_to_none():
    """Convert empty CSV fields into SQL NULL-compatible values."""
    rows = [
        ["product_1", "", "40", "", "1"],
    ]

    prepared = prepare_products(rows)

    assert prepared == [
        ("product_1", None, "40", None, "1"),
    ]
