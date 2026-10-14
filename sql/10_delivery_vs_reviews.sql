
-- ============================================================
-- PROJECT: E-Commerce Intelligence
-- ANALYSIS: Delivery Performance vs Customer Satisfaction
-- DATABASE: PostgreSQL
-- ============================================================

-- Business rules:
-- 1. Analyze delivered orders with valid delivery dates.
-- 2. Exclude inconsistent carrier/delivery timestamps.
-- 3. Define late delivery using calendar dates.
-- 4. Aggregate multiple reviews into one score per order.
-- 5. Compare only orders with at least one review.
-- 6. Report association, not causation.

WITH valid_deliveries AS (
    SELECT
        order_id,
        CASE
            WHEN order_delivered_customer_date::DATE
                 > order_estimated_delivery_date::DATE
            THEN 'Late'
            ELSE 'On Time'
        END AS delivery_status
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
reviews_per_order AS (
    SELECT
        order_id,
        AVG(review_score::NUMERIC) AS avg_review_score,
        COUNT(*) AS review_count
    FROM reviews
    GROUP BY order_id
),
combined AS (
    SELECT
        d.order_id,
        d.delivery_status,
        r.avg_review_score,
        r.review_count
    FROM valid_deliveries AS d
    INNER JOIN reviews_per_order AS r
        ON d.order_id = r.order_id
)
SELECT
    delivery_status,
    COUNT(*) AS reviewed_orders,
    ROUND(
        AVG(avg_review_score),
        2
    ) AS avg_review_score,
    COUNT(*) FILTER (
        WHERE avg_review_score <= 2
    ) AS low_rated_orders,
    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE avg_review_score <= 2
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS low_rating_rate_pct,
    ROUND(
        AVG(review_count),
        2
    ) AS avg_reviews_per_order
FROM combined
GROUP BY delivery_status
ORDER BY
    CASE delivery_status
        WHEN 'On Time' THEN 1
        ELSE 2
    END;
