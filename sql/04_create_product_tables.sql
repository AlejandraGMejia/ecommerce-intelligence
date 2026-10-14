
-- ============================================================
-- PROJECT: E-Commerce Intelligence
-- MODULE: Product Category Analysis
-- PURPOSE: Extend the existing relational model
-- DATABASE: PostgreSQL
-- ============================================================

BEGIN;

-- Product category translations.
-- Categories are preserved in their original Portuguese names.

CREATE TABLE IF NOT EXISTS product_categories (
    product_category_name VARCHAR(100) PRIMARY KEY,
    product_category_name_english VARCHAR(100) NOT NULL
);

-- Product catalog.
-- Nullable attributes preserve missing source information.

CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(32) PRIMARY KEY,
    product_category_name VARCHAR(100),
    product_name_length INTEGER,
    product_description_length INTEGER,
    product_photos_qty INTEGER,
    product_weight_g INTEGER,
    product_length_cm INTEGER,
    product_height_cm INTEGER,
    product_width_cm INTEGER,

    CONSTRAINT products_name_length_nonnegative
        CHECK (
            product_name_length IS NULL
            OR product_name_length >= 0
        ),

    CONSTRAINT products_description_length_nonnegative
        CHECK (
            product_description_length IS NULL
            OR product_description_length >= 0
        ),

    CONSTRAINT products_photos_nonnegative
        CHECK (
            product_photos_qty IS NULL
            OR product_photos_qty >= 0
        ),

    CONSTRAINT products_weight_nonnegative
        CHECK (
            product_weight_g IS NULL
            OR product_weight_g >= 0
        ),

    CONSTRAINT products_dimensions_nonnegative
        CHECK (
            (product_length_cm IS NULL OR product_length_cm >= 0)
            AND (product_height_cm IS NULL OR product_height_cm >= 0)
            AND (product_width_cm IS NULL OR product_width_cm >= 0)
        )
);

CREATE INDEX IF NOT EXISTS idx_products_category
    ON products (product_category_name);

COMMIT;