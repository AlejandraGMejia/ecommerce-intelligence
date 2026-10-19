
-- ============================================================
-- PROJECT: E-Commerce Intelligence
-- MODULE: BI Product Category Performance
-- SOURCE: Olist Brazilian E-Commerce Dataset
-- CURRENCY: BRL
--
-- GRAIN: One row per product category.
--
-- BUSINESS RULES:
-- 1. Include only delivered orders.
-- 2. Exclude freight from item value.
-- 3. Count each order once per category.
-- 4. Preserve untranslated and missing categories.
-- 5. Item value is not net revenue or profit.
--
-- The dataset covers the complete historical period,
-- matching the original category analysis.
-- ============================================================

WITH category_order_values AS (
    SELECT
        COALESCE(
            pc.product_category_name_english,
            p.product_category_name,
            'Uncategorized'
        ) AS category,

        oi.order_id,

        SUM(oi.price) AS order_category_item_value

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
        ),
        oi.order_id
),

category_metrics AS (
    SELECT
        category,

        COUNT(*) AS delivered_orders,

        ROUND(
            SUM(order_category_item_value),
            2
        ) AS item_value_brl,

        ROUND(
            AVG(order_category_item_value),
            2
        ) AS avg_order_category_value_brl

    FROM category_order_values

    GROUP BY category
),

category_shares AS (
    SELECT
        category,
        delivered_orders,
        item_value_brl,
        avg_order_category_value_brl,

        ROUND(
            100.0 * item_value_brl
            / NULLIF(SUM(item_value_brl) OVER (), 0),
            2
        ) AS item_value_share_pct

    FROM category_metrics
)

SELECT
    ROW_NUMBER() OVER (
        ORDER BY item_value_brl DESC, category
    ) AS category_rank,

    category,
    delivered_orders,
    item_value_brl,
    avg_order_category_value_brl,
    item_value_share_pct

FROM category_shares

ORDER BY category_rank;
