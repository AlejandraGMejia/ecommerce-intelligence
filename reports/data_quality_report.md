
# Data Quality Assessment

## Project
E-Commerce Intelligence — Olist Dataset

## Scope
Initial validation of orders, customers, and order items.

## Data Volume

| Table | Rows |
|---|---:|
| Orders | 99,441 |
| Customers | 99,441 |
| Order Items | 112,650 |

## Key Integrity

- Duplicate order IDs: 0
- Duplicate customer IDs: 0
- Duplicate (order_id, order_item_id) keys: 0
- Orders referencing missing customers: 0
- Order items referencing missing orders: 0

## Missing Values

In the orders table:

- order_approved_at: 160
- order_delivered_carrier_date: 1,783
- order_delivered_customer_date: 2,965

No missing values were detected in the customers or order_items tables.

## Findings

1. Most orders have a delivered status (96,478).
2. Missing delivery dates are strongly associated with non-delivered order statuses.
3. Eight delivered orders have no recorded customer delivery date.
4. Six canceled orders have a recorded customer delivery date.

## Recommendations

- Preserve raw data without modification.
- Investigate exceptional records before applying cleaning rules.
- Convert timestamp columns to appropriate datetime types.
- Validate business rules using order status and delivery dates.
- Continue checking uniqueness, completeness, and consistency in the remaining tables.

## Status

Initial data quality assessment completed for three tables.
Further validation is required.
