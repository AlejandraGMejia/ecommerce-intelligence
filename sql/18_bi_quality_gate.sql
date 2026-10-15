
-- ============================================================
-- E-COMMERCE INTELLIGENCE
-- Module 7: BI Data Mart Quality Gate
--
-- Returns one row containing:
--   total_checks
--   passed_checks
--   failed_checks
--   quality_status
--
-- Read-only validation.
-- ============================================================

WITH metrics AS (
    SELECT
        COUNT(*) AS delivered_orders,

        COUNT(DISTINCT order_id) AS distinct_orders,

        COUNT(*) FILTER (
            WHERE order_id IS NULL
               OR customer_unique_id IS NULL
               OR order_purchase_timestamp IS NULL
        ) AS missing_required_values,

        COUNT(*) FILTER (
            WHERE item_count <= 0
               OR item_value_brl IS NULL
               OR item_value_brl <= 0
               OR freight_value_brl IS NULL
               OR freight_value_brl < 0
        ) AS invalid_item_metrics,

        COUNT(*) FILTER (
            WHERE purchase_month IS DISTINCT FROM
                  DATE_TRUNC(
                      'month',
                      order_purchase_timestamp
                  )::DATE
        ) AS invalid_purchase_months,

        COALESCE(SUM(item_count), 0) AS delivered_items,

        COALESCE(SUM(item_value_brl), 0)
            AS total_item_value_brl,

        COUNT(DISTINCT customer_unique_id)
            AS unique_buyers,

        COUNT(DISTINCT customer_state)
            AS geographic_units

    FROM analytics_order_summary
),

checks AS (
    SELECT
        delivered_orders = distinct_orders AS passed
    FROM metrics

    UNION ALL

    SELECT missing_required_values = 0
    FROM metrics

    UNION ALL

    SELECT invalid_item_metrics = 0
    FROM metrics

    UNION ALL

    SELECT invalid_purchase_months = 0
    FROM metrics

    UNION ALL

    SELECT delivered_orders = 96478
    FROM metrics

    UNION ALL

    SELECT delivered_items = 110197
    FROM metrics

    UNION ALL

    SELECT ABS(
        total_item_value_brl - 13221498.11
    ) <= 0.01
    FROM metrics

    UNION ALL

    SELECT unique_buyers = 93358
    FROM metrics

    UNION ALL

    SELECT geographic_units = 27
    FROM metrics
)

SELECT
    COUNT(*) AS total_checks,

    COUNT(*) FILTER (
        WHERE passed IS TRUE
    ) AS passed_checks,

    COUNT(*) FILTER (
        WHERE passed IS NOT TRUE
    ) AS failed_checks,

    CASE
        WHEN BOOL_AND(passed IS TRUE)
        THEN 'PASSED'
        ELSE 'FAILED'
    END AS quality_status

FROM checks;
