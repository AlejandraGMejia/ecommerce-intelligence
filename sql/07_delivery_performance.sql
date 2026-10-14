
-- ============================================================
-- PROJECT: E-Commerce Intelligence
-- MODULE: Delivery Performance
-- SOURCE: Olist Brazilian E-Commerce Dataset
-- DATABASE: PostgreSQL
-- ============================================================

-- Business rules:
-- 1. Analyze delivered orders only.
-- 2. Require purchase, actual delivery, and estimated dates.
-- 3. Exclude chronologically inconsistent carrier/delivery dates.
-- 4. Preserve anomalous records in the source table.
-- 5. Count delivery as on time when its calendar date is
--    on or before the estimated delivery date.

WITH valid_deliveries AS (
    SELECT
        order_id,
        order_purchase_timestamp,
        order_delivered_customer_date,
        order_estimated_delivery_date,
        EXTRACT(
            EPOCH FROM (
                order_delivered_customer_date
                - order_purchase_timestamp
            )
        ) / 86400.0 AS delivery_days
    FROM orders
    WHERE order_status = 'delivered'
      AND order_purchase_timestamp IS NOT NULL
      AND order_delivered_customer_date IS NOT NULL
      AND order_estimated_delivery_date IS NOT NULL
      AND order_delivered_customer_date
          >= order_purchase_timestamp
      AND (
          order_delivered_carrier_date IS NULL
          OR order_delivered_customer_date
              >= order_delivered_carrier_date
      )
),
delivery_metrics AS (
    SELECT
        COUNT(*) AS valid_delivered_orders,

        COUNT(*) FILTER (
            WHERE order_delivered_customer_date::DATE
                  <= order_estimated_delivery_date::DATE
        ) AS on_time_orders,

        COUNT(*) FILTER (
            WHERE order_delivered_customer_date::DATE
                  > order_estimated_delivery_date::DATE
        ) AS late_orders,

        ROUND(
            AVG(delivery_days)::NUMERIC,
            2
        ) AS avg_delivery_days,

        ROUND(
            AVG(
                EXTRACT(
                    EPOCH FROM (
                        order_delivered_customer_date
                        - order_estimated_delivery_date
                    )
                ) / 86400.0
            ) FILTER (
                WHERE order_delivered_customer_date::DATE
                      > order_estimated_delivery_date::DATE
            )::NUMERIC,
            2
        ) AS avg_late_days
    FROM valid_deliveries
)
SELECT
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
    ) AS late_rate_pct,
    avg_delivery_days,
    avg_late_days
FROM delivery_metrics;
