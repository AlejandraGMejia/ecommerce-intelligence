
-- ============================================================
-- E-COMMERCE INTELLIGENCE
-- Module 4: Geographic Sales Analysis
--
-- Objective:
-- Compare delivered-order activity and item value by
-- customer state.
--
-- Monetary values exclude freight and do not represent
-- net revenue or profit.
-- ============================================================

WITH delivered_order_values AS (
    SELECT
        o.order_id,
        c.customer_state,
        c.customer_city,
        SUM(oi.price) AS order_item_value
    FROM orders AS o
    INNER JOIN customers AS c
        ON o.customer_id = c.customer_id
    INNER JOIN order_items AS oi
        ON o.order_id = oi.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY
        o.order_id,
        c.customer_state,
        c.customer_city
),

state_performance AS (
    SELECT
        customer_state,
        COUNT(*) AS delivered_orders,
        SUM(order_item_value) AS total_item_value,
        AVG(order_item_value) AS avg_order_item_value
    FROM delivered_order_values
    GROUP BY customer_state
)

SELECT
    customer_state,
    delivered_orders,
    ROUND(total_item_value, 2) AS total_item_value_brl,
    ROUND(avg_order_item_value, 2) AS avg_order_item_value_brl,
    ROUND(
        100.0 * total_item_value
        / SUM(total_item_value) OVER (),
        2
    ) AS item_value_share_pct,
    ROUND(
        100.0 * delivered_orders
        / SUM(delivered_orders) OVER (),
        2
    ) AS order_share_pct
FROM state_performance
ORDER BY total_item_value_brl DESC;
