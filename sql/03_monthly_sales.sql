
-- ============================================================
-- PROJECT: E-Commerce Intelligence
-- ANALYSIS: Monthly Sales Performance
-- SOURCE: Olist Brazilian E-Commerce Dataset
-- DATABASE: PostgreSQL
-- CURRENCY: BRL
-- ============================================================

-- Business rules:
-- 1. Include only delivered orders.
-- 2. Aggregate item values at the order level first.
-- 3. Group orders by their purchase month.
-- 4. Calculate month-over-month growth only for
--    consecutive calendar months.
-- 5. Preserve NULL when a valid comparison is unavailable.
-- 6. Monetary values represent item value, not net revenue.


WITH delivered_orders AS (
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
),

monthly_metrics AS (
    SELECT
        purchase_month,

        COUNT(*) AS delivered_orders,

        ROUND(
            SUM(item_value),
            2
        ) AS item_value_brl,

        ROUND(
            AVG(item_value),
            2
        ) AS avg_order_value_brl

    FROM delivered_orders

    GROUP BY purchase_month
),

previous_month_metrics AS (
    SELECT
        purchase_month,
        delivered_orders,
        item_value_brl,
        avg_order_value_brl,

        LAG(purchase_month) OVER (
            ORDER BY purchase_month
        ) AS previous_month,

        LAG(item_value_brl) OVER (
            ORDER BY purchase_month
        ) AS previous_month_value

    FROM monthly_metrics
)

SELECT
    purchase_month,
    delivered_orders,
    item_value_brl,
    avg_order_value_brl,

    CASE
        WHEN previous_month = (
            purchase_month - INTERVAL '1 month'
        )::DATE

        THEN ROUND(
            100.0 * (
                item_value_brl - previous_month_value
            ) / NULLIF(previous_month_value, 0),
            2
        )

        ELSE NULL
    END AS monthly_growth_pct

FROM previous_month_metrics

ORDER BY purchase_month;
