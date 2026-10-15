
-- ============================================================
-- E-COMMERCE INTELLIGENCE
-- Module 5: Monthly Customer Cohort Retention
--
-- Business rules:
-- - Include only delivered orders.
-- - Use customer_unique_id to identify buyers.
-- - Group buyers by their first delivered order's
--   purchase month.
-- - Count each buyer once per activity month.
-- - Retention measures subsequent calendar-month activity.
-- - Exclude incomplete calendar months after August 2018.
-- ============================================================

WITH delivered_purchases AS (
    SELECT DISTINCT
        c.customer_unique_id,
        o.order_id,
        DATE_TRUNC(
            'month',
            o.order_purchase_timestamp
        )::DATE AS purchase_month
    FROM orders AS o
    INNER JOIN customers AS c
        ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp IS NOT NULL
),

first_purchase AS (
    SELECT
        customer_unique_id,
        MIN(purchase_month) AS cohort_month
    FROM delivered_purchases
    GROUP BY customer_unique_id
),

monthly_activity AS (
    SELECT DISTINCT
        dp.customer_unique_id,
        fp.cohort_month,
        dp.purchase_month,
        (
            (
                EXTRACT(YEAR FROM dp.purchase_month)
                - EXTRACT(YEAR FROM fp.cohort_month)
            ) * 12
            +
            (
                EXTRACT(MONTH FROM dp.purchase_month)
                - EXTRACT(MONTH FROM fp.cohort_month)
            )
        )::INTEGER AS cohort_age_months
    FROM delivered_purchases AS dp
    INNER JOIN first_purchase AS fp
        ON dp.customer_unique_id = fp.customer_unique_id
),

cohort_sizes AS (
    SELECT
        cohort_month,
        COUNT(*) AS cohort_size
    FROM first_purchase
    GROUP BY cohort_month
),

retention AS (
    SELECT
        ma.cohort_month,
        ma.cohort_age_months,
        COUNT(DISTINCT ma.customer_unique_id)
            AS active_buyers
    FROM monthly_activity AS ma
    WHERE ma.purchase_month >= DATE '2017-01-01'
      AND ma.purchase_month < DATE '2018-09-01'
    GROUP BY
        ma.cohort_month,
        ma.cohort_age_months
)

SELECT
    r.cohort_month,
    cs.cohort_size,
    r.cohort_age_months,
    r.active_buyers,
    ROUND(
        100.0 * r.active_buyers
        / NULLIF(cs.cohort_size, 0),
        2
    ) AS retention_rate_pct
FROM retention AS r
INNER JOIN cohort_sizes AS cs
    ON r.cohort_month = cs.cohort_month
WHERE r.cohort_month >= DATE '2017-01-01'
  AND r.cohort_month < DATE '2018-09-01'
ORDER BY
    r.cohort_month,
    r.cohort_age_months;
