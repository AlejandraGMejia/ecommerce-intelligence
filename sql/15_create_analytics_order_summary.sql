
-- ============================================================
-- E-COMMERCE INTELLIGENCE
-- Module 7: Analytics Data Mart
--
-- View: analytics_order_summary
--
-- Grain:
--   One row per delivered order.
--
-- Monetary definitions:
--   item_value_brl = sum of item prices, excluding freight.
--   freight_value_brl = sum of freight charges.
--
-- This view does not modify the original source tables.
-- ============================================================

CREATE OR REPLACE VIEW analytics_order_summary AS

WITH item_aggregates AS (
    SELECT
        oi.order_id,
        COUNT(*) AS item_count,
        SUM(oi.price) AS item_value_brl,
        SUM(oi.freight_value) AS freight_value_brl
    FROM order_items AS oi
    GROUP BY oi.order_id
)

SELECT
    o.order_id,
    c.customer_unique_id,
    c.customer_state,
    c.customer_city,

    o.order_status,

    o.order_purchase_timestamp,
    DATE_TRUNC(
        'month',
        o.order_purchase_timestamp
    )::DATE AS purchase_month,

    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,

    ia.item_count,
    ia.item_value_brl,
    ia.freight_value_brl,

    CASE
        WHEN o.order_delivered_customer_date IS NOT NULL
         AND o.order_estimated_delivery_date IS NOT NULL
        THEN (
            o.order_delivered_customer_date::DATE
            > o.order_estimated_delivery_date::DATE
        )
        ELSE NULL
    END AS is_late_delivery

FROM orders AS o

INNER JOIN customers AS c
    ON o.customer_id = c.customer_id

INNER JOIN item_aggregates AS ia
    ON o.order_id = ia.order_id

WHERE o.order_status = 'delivered'
  AND o.order_purchase_timestamp IS NOT NULL;
