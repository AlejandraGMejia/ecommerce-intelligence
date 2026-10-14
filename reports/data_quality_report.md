
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

## Business Rule Investigation

### Summary

Six business rules were evaluated across the orders and order items datasets.

Four rules returned zero violations.

Two rules identified a total of 31 distinct affected orders.

### Carrier Handoff Anomalies

- Affected orders: 23
- Minimum temporal inversion: 0.39 hours
- Median temporal inversion: 39.86 hours
- Mean temporal inversion: 78.46 hours
- Maximum temporal inversion: 386.31 hours

All 23 affected orders have a delivered status.

These records contain customer delivery timestamps earlier than
their recorded carrier handoff timestamps.

### Missing Delivery Timestamps

Eight orders have a delivered status but no customer delivery timestamp.

Seven have a recorded carrier handoff timestamp.
One has neither a carrier handoff nor a customer delivery timestamp.

### Overlap

No orders are affected by both anomaly categories.

### Data Quality Policy

1. Preserve all original source records.
2. Do not infer or fabricate missing delivery timestamps.
3. Flag inconsistent temporal sequences for investigation.
4. Exclude reversed carrier-to-customer intervals from
   transportation-duration metrics.
5. Exclude missing customer delivery timestamps from metrics
   requiring actual delivery dates.
6. Retain otherwise valid records for unrelated analyses.
7. Document exclusions and denominators for calculated KPIs.

### Limitations

The dataset does not provide sufficient information to determine
the root cause of timestamp inconsistencies.

Anomalies are identified using reproducible rules, rather than
automatically classified as incorrect source records.
