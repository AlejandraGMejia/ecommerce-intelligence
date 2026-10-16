
-- ============================================================
-- E-COMMERCE INTELLIGENCE
-- Module 7: Executive BI KPI Dataset
--
-- Grain: One row for the complete reporting period.
-- Reporting period: January 2017 - August 2018.
--
-- Business rules:
-- - Delivered orders only.
-- - Purchase date determines reporting period.
-- - Item value excludes freight.
-- - Average Order Value is calculated as:
--   Total Item Value / Delivered Orders.
-- - Distinct buyers are counted across the entire period.
--
-- Source: analytics_order_summary
-- Read-only analytical query.
-- ============================================================

WITH reporting_period AS (
    SELECT
        order_id,
        customer_unique_id,
        item_count,
        item_value_brl,
        freight_value_brl
    FROM analytics_order_summary
    WHERE purchase_month >= DATE '2017-01-01'
      AND purchase_month < DATE '2018-09-01'
)

SELECT
    DATE '2017-01-01' AS period_start,
    DATE '2018-08-31' AS period_end,

    COUNT(*) AS delivered_orders,

    COUNT(DISTINCT customer_unique_id)
        AS unique_buyers,

    COALESCE(SUM(item_count), 0)
        AS delivered_items,

    ROUND(
        COALESCE(SUM(item_value_brl), 0),
        2
    ) AS item_value_brl,

    ROUND(
        COALESCE(SUM(item_value_brl), 0)
        / NULLIF(COUNT(*), 0),
        2
    ) AS average_order_value_brl,

    ROUND(
        COALESCE(SUM(freight_value_brl), 0),
        2
    ) AS freight_value_brl

FROM reporting_period;
