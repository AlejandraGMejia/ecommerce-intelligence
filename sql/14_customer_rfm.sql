
-- ============================================================
-- E-COMMERCE INTELLIGENCE
-- Module 6: Customer Segmentation & RFM Analysis
--
-- Reference date: 2018-09-01
--
-- R: Days since last delivered-order purchase
-- F: Number of delivered orders
-- M: Total item value excluding freight
--
-- Rules are descriptive, not predictive.
-- ============================================================

WITH parameters AS (
    SELECT DATE '2018-09-01' AS reference_date
),

order_values AS (
    SELECT
        o.order_id,
        c.customer_unique_id,
        o.order_purchase_timestamp::DATE AS purchase_date,
        SUM(oi.price) AS order_item_value
    FROM orders AS o
    JOIN customers AS c
        ON o.customer_id = c.customer_id
    JOIN order_items AS oi
        ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp IS NOT NULL
    GROUP BY
        o.order_id,
        c.customer_unique_id,
        o.order_purchase_timestamp::DATE
),

customer_rfm AS (
    SELECT
        ov.customer_unique_id,
        p.reference_date - MAX(ov.purchase_date)
            AS recency_days,
        COUNT(*) AS frequency,
        SUM(ov.order_item_value) AS monetary_value
    FROM order_values AS ov
    CROSS JOIN parameters AS p
    GROUP BY
        ov.customer_unique_id,
        p.reference_date
),

scored_customers AS (
    SELECT
        customer_unique_id,
        recency_days,
        frequency,
        monetary_value,
        CASE
            WHEN recency_days <= 90 THEN 3
            WHEN recency_days <= 180 THEN 2
            ELSE 1
        END AS r_score,
        CASE
            WHEN frequency >= 3 THEN 3
            WHEN frequency = 2 THEN 2
            ELSE 1
        END AS f_score,
        CASE
            WHEN monetary_value >= 300 THEN 3
            WHEN monetary_value >= 150 THEN 2
            ELSE 1
        END AS m_score
    FROM customer_rfm
),

segmented_customers AS (
    SELECT
        *,
        CASE
            WHEN frequency >= 2
                 AND recency_days <= 90
                 AND monetary_value >= 150
                THEN 'Champions'

            WHEN frequency >= 2
                 AND recency_days <= 180
                THEN 'Loyal Customers'

            WHEN frequency >= 2
                 AND recency_days > 180
                THEN 'At-Risk Repeat Buyers'

            WHEN frequency = 1
                 AND recency_days <= 90
                THEN 'Recent One-Time Buyers'

            WHEN frequency = 1
                 AND recency_days > 90
                 AND monetary_value >= 300
                THEN 'High-Value One-Time Buyers'

            WHEN frequency = 1
                 AND recency_days <= 180
                THEN 'Developing One-Time Buyers'

            ELSE 'Inactive One-Time Buyers'
        END AS customer_segment
    FROM scored_customers
)

SELECT
    customer_segment,
    COUNT(*) AS customers,
    ROUND(
        100.0 * COUNT(*)
        / SUM(COUNT(*)) OVER (),
        2
    ) AS customer_share_pct,
    ROUND(AVG(recency_days), 2)
        AS avg_recency_days,
    ROUND(AVG(frequency), 2)
        AS avg_frequency,
    ROUND(AVG(monetary_value), 2)
        AS avg_monetary_value_brl,
    ROUND(SUM(monetary_value), 2)
        AS total_item_value_brl
FROM segmented_customers
GROUP BY customer_segment
ORDER BY total_item_value_brl DESC;
