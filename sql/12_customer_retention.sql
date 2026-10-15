
-- ============================================================
-- E-COMMERCE INTELLIGENCE
-- Module 5: Customer Retention & Cohort Analysis
--
-- Analysis 1: Customer repeat purchase behavior
--
-- Business rules:
-- - Only delivered orders are included.
-- - customer_unique_id identifies an individual buyer.
-- - A repeat buyer has at least two delivered orders.
-- - Repeat purchase rate is not cohort retention.
-- ============================================================

WITH customer_orders AS (
    SELECT
        c.customer_unique_id,
        COUNT(DISTINCT o.order_id) AS delivered_orders,
        MIN(o.order_purchase_timestamp) AS first_purchase,
        MAX(o.order_purchase_timestamp) AS last_purchase
    FROM customers AS c
    INNER JOIN orders AS o
        ON c.customer_id = o.customer_id
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp IS NOT NULL
    GROUP BY c.customer_unique_id
),

customer_summary AS (
    SELECT
        COUNT(*) AS unique_buyers,
        COUNT(*) FILTER (
            WHERE delivered_orders = 1
        ) AS one_time_buyers,
        COUNT(*) FILTER (
            WHERE delivered_orders >= 2
        ) AS repeat_buyers,
        SUM(delivered_orders) AS total_delivered_orders,
        MAX(delivered_orders) AS max_orders_per_buyer,
        AVG(delivered_orders) AS avg_orders_per_buyer
    FROM customer_orders
)

SELECT
    unique_buyers,
    one_time_buyers,
    repeat_buyers,
    total_delivered_orders,
    ROUND(
        100.0 * repeat_buyers
        / NULLIF(unique_buyers, 0),
        2
    ) AS repeat_buyer_rate_pct,
    ROUND(
        avg_orders_per_buyer,
        2
    ) AS avg_orders_per_buyer,
    max_orders_per_buyer
FROM customer_summary;


-- ============================================================
-- Analysis 2: Distribution of delivered orders per buyer
-- ============================================================

WITH customer_orders AS (
    SELECT
        c.customer_unique_id,
        COUNT(DISTINCT o.order_id) AS delivered_orders
    FROM customers AS c
    INNER JOIN orders AS o
        ON c.customer_id = o.customer_id
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp IS NOT NULL
    GROUP BY c.customer_unique_id
)

SELECT
    delivered_orders AS orders_per_buyer,
    COUNT(*) AS buyer_count,
    ROUND(
        100.0 * COUNT(*)
        / SUM(COUNT(*)) OVER (),
        2
    ) AS buyer_share_pct
FROM customer_orders
GROUP BY delivered_orders
ORDER BY delivered_orders;
