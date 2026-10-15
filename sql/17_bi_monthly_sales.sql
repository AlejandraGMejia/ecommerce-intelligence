
-- ============================================================
-- E-COMMERCE INTELLIGENCE
-- Module 7: BI-Ready Monthly Sales Dataset
--
-- Grain: One row per purchase month.
-- Source: analytics_order_summary
--
-- Item values exclude freight.
-- Results are historical, not live sales.
-- ============================================================

SELECT
    purchase_month,

    COUNT(*) AS delivered_orders,

    COUNT(DISTINCT customer_unique_id) AS unique_buyers,

    SUM(item_count) AS delivered_items,

    ROUND(
        SUM(item_value_brl),
        2
    ) AS item_value_brl,

    ROUND(
        SUM(item_value_brl) / NULLIF(COUNT(*), 0),
        2
    ) AS avg_item_value_per_order_brl,

    ROUND(
        SUM(freight_value_brl),
        2
    ) AS freight_value_brl

FROM analytics_order_summary

WHERE purchase_month >= DATE '2017-01-01'
  AND purchase_month < DATE '2018-09-01'

GROUP BY purchase_month

ORDER BY purchase_month;
