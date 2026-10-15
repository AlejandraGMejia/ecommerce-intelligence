
-- ============================================================
-- E-COMMERCE INTELLIGENCE
-- Module 7: Data Mart Quality Validation
--
-- Validates analytics_order_summary.
-- Read-only: does not change database records.
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

        COALESCE(SUM(item_value_brl), 0) AS total_item_value_brl,

        COUNT(DISTINCT customer_unique_id) AS unique_buyers,

        COUNT(DISTINCT customer_state) AS geographic_units

    FROM analytics_order_summary
),

checks AS (
    SELECT
        'Unique order grain' AS check_name,
        delivered_orders = distinct_orders AS passed
    FROM metrics

    UNION ALL

    SELECT
        'No missing required values',
        missing_required_values = 0
    FROM metrics

    UNION ALL

    SELECT
        'Valid item metrics',
        invalid_item_metrics = 0
    FROM metrics

    UNION ALL

    SELECT
        'Valid purchase month',
        invalid_purchase_months = 0
    FROM metrics

    UNION ALL

    SELECT
        'Delivered order count',
        delivered_orders = 96478
    FROM metrics

    UNION ALL

    SELECT
        'Delivered item count',
        delivered_items = 110197
    FROM metrics

    UNION ALL

    SELECT
        'Delivered item value',
        ABS(
            total_item_value_brl - 13221498.11
        ) <= 0.01
    FROM metrics

    UNION ALL

    SELECT
        'Unique buyer count',
        unique_buyers = 93358
    FROM metrics

    UNION ALL

    SELECT
        'Geographic coverage',
        geographic_units = 27
    FROM metrics
)

SELECT
    check_name,
    CASE
        WHEN passed THEN 'PASSED'
        ELSE 'FAILED'
    END AS status
FROM checks
ORDER BY check_name;
