
-- ============================================================
-- PROJECT: E-Commerce Intelligence
-- ANALYSIS: Monthly Delivery Performance
-- DATABASE: PostgreSQL
-- ============================================================

-- Delivery performance is grouped by purchase month.
-- An order is late if its actual delivery calendar date
-- is after the estimated delivery calendar date.

WITH valid_deliveries AS (
    SELECT
        order_id,
        DATE_TRUNC(
            'month',
            order_purchase_timestamp
        )::DATE AS purchase_month,
        order_delivered_customer_date::DATE AS actual_date,
        order_estimated_delivery_date::DATE AS estimated_date
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
monthly_metrics AS (
    SELECT
        purchase_month,
        COUNT(*) AS valid_delivered_orders,
        COUNT(*) FILTER (
            WHERE actual_date <= estimated_date
        ) AS on_time_orders,
        COUNT(*) FILTER (
            WHERE actual_date > estimated_date
        ) AS late_orders
    FROM valid_deliveries
    WHERE purchase_month >= DATE '2017-01-01'
      AND purchase_month < DATE '2018-09-01'
    GROUP BY purchase_month
)
SELECT
    purchase_month,
    valid_delivered_orders,
    on_time_orders,
    late_orders,
    ROUND(
        100.0 * on_time_orders
        / NULLIF(valid_delivered_orders, 0),
        2
    ) AS on_time_rate_pct,
    ROUND(
        100.0 * late_orders
        / NULLIF(valid_delivered_orders, 0),
        2
    ) AS late_rate_pct
FROM monthly_metrics
ORDER BY purchase_month;
