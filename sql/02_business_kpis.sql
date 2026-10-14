
-- E-Commerce Intelligence
-- Executive KPIs: initial business overview
-- Monetary amounts are in Brazilian reais (BRL).

WITH order_values AS (
    SELECT
        o.order_id,
        o.order_status,
        o.order_purchase_timestamp,
        SUM(oi.price) AS item_value,
        SUM(oi.freight_value) AS freight_value
    FROM orders AS o
    LEFT JOIN order_items AS oi
        ON o.order_id = oi.order_id
    GROUP BY
        o.order_id,
        o.order_status,
        o.order_purchase_timestamp
)

SELECT
    COUNT(*) AS total_orders,

    COUNT(*) FILTER (
        WHERE order_status = 'delivered'
    ) AS delivered_orders,

    COUNT(*) FILTER (
        WHERE order_status = 'canceled'
    ) AS canceled_orders,

    COUNT(*) FILTER (
        WHERE item_value IS NOT NULL
    ) AS orders_with_items,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE order_status = 'delivered'
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS delivered_order_percentage,

    ROUND(
        SUM(item_value) FILTER (
            WHERE order_status = 'delivered'
        ),
        2
    ) AS delivered_item_value_brl,

    ROUND(
        AVG(item_value) FILTER (
            WHERE order_status = 'delivered'
        ),
        2
    ) AS avg_delivered_order_item_value_brl

FROM order_values;
