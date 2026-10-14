
# E-Commerce Intelligence

**End-to-End Data Analytics & Data Engineering Portfolio Project**

An end-to-end e-commerce analytics project based on the Brazilian E-Commerce Public Dataset by Olist.

This project transforms historical transactional data into actionable business insights using Python, PostgreSQL, SQL, data quality validation, automated testing, and executive visualizations.

**Status:** In Development

## 1. Project Overview

The objective is to demonstrate practical Data Analytics and Data Engineering skills through a reproducible e-commerce data workflow.

The project combines:

- Data exploration and quality assessment
- Python-based data ingestion
- PostgreSQL relational modeling
- SQL business analysis
- Executive data visualization
- Automated testing
- Business insight communication

### Business Questions

1. How has e-commerce activity evolved over time?
2. Which product categories contribute the most monetary value?
3. How efficiently are orders delivered?
4. Are late deliveries associated with lower customer satisfaction?
5. Which geographic regions generate the most business activity?
6. How do customer retention and purchasing patterns evolve?

The first four questions have been investigated. Geographic analysis and customer retention are planned.

## 2. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Data ingestion, validation, and visualization |
| Pandas | Data exploration and transformation |
| PostgreSQL | Relational storage and integrity constraints |
| SQL | Business analytics and KPI calculations |
| Matplotlib | Executive visualizations |
| Pytest | Automated testing |
| Ruff | Python linting and formatting |
| Git & GitHub | Version control |

## 3. Data Architecture

The project follows a modular workflow:

1. **Source Data:** Historical Olist CSV files.
2. **Data Exploration:** Schema inspection, missing values, duplicates, and anomalies.
3. **Data Ingestion:** Python scripts load data into PostgreSQL.
4. **Relational Modeling:** Primary and foreign keys enforce integrity.
5. **Data Validation:** Checks verify source structure, counts, and relationships.
6. **Business Analysis:** SQL queries calculate operational and commercial metrics.
7. **Visualization:** Python scripts generate executive charts.
8. **Quality Assurance:** Pytest and Ruff support code reliability.

### Implemented Database Tables

| Table | Description | Records |
|---|---|---:|
| `customers` | Customer and location information | 99,441 |
| `orders` | Order status and timestamps | 99,441 |
| `order_items` | Products and item-level monetary values | 112,650 |
| `products` | Product catalog and attributes | 32,951 |
| `product_categories` | Category translations | 71 |
| `reviews` | Customer review records | 99,224 |

### Referential Integrity

The relational model includes:

- `orders.customer_id` → `customers.customer_id`
- `order_items.order_id` → `orders.order_id`
- `order_items.product_id` → `products.product_id`
- `reviews.order_id` → `orders.order_id`

The `reviews` table uses an internal primary key because source `review_id` values are not unique.

Product category translations are joined using the original category names. Missing translations are preserved rather than discarded.

## 4. Business Analysis

### 4.1 Overall E-Commerce Performance

The analysis focuses on delivered orders and item values, excluding freight.

| KPI | Result |
|---|---:|
| Total orders | 99,441 |
| Delivered orders | 96,478 |
| Delivery completion rate | 97.02% |
| Delivered-order item value | R$ 13,221,498.11 |
| Average delivered-order item value | R$ 137.04 |
| Delivered order items | 110,197 |

**Metric definition:** Delivered-order item value is the sum of product prices associated with orders marked as delivered.

It does not represent collected payments, net revenue, or profit.

### 4.2 Monthly E-Commerce Performance

Monthly performance is calculated using the purchase month of delivered orders.

![Monthly E-Commerce Performance](reports/figures/monthly_sales_executive.png)

**Key Findings**

- November 2017 recorded the highest monthly delivered-order item value: approximately **R$ 987,765**.
- This represented a **52.37% increase** compared with October 2017.
- The main visualization covers January 2017 through August 2018.

The dataset contains sparse activity in parts of 2016. Month-over-month growth is calculated only when consecutive calendar months are available.

### 4.3 Product Category Performance

Product categories are ranked by the value of items associated with delivered orders.

![Top 10 Product Categories](reports/figures/top_categories.png)

**Key Findings**

- `health_beauty` leads with approximately **R$ 1.23 million**.
- `watches_gifts` follows with approximately **R$ 1.17 million**.
- `bed_bath_table` ranks third with approximately **R$ 1.02 million**.
- The five leading categories account for approximately **39.83%** of delivered-order item value.
- `bed_bath_table` appears in more delivered orders than `health_beauty`, demonstrating that order volume and monetary contribution measure different aspects of performance.

Category-level order counts use distinct orders within each category.

An order containing products from multiple categories may contribute to multiple category counts.

### 4.4 Delivery Performance

Delivery performance is evaluated using delivered orders with valid purchase, estimated delivery, and actual delivery timestamps.

An order is considered late when its actual delivery calendar date is after the estimated delivery calendar date.

![Monthly Late Delivery Rate](reports/figures/monthly_delivery_performance.png)

**Overall Delivery KPIs**

| Metric | Result |
|---|---:|
| Valid delivered orders | 96,447 |
| On-time orders | 89,913 |
| Late orders | 6,534 |
| On-time delivery rate | 93.23% |
| Late delivery rate | 6.77% |
| Average purchase-to-delivery time | 12.56 days |
| Average delay among late deliveries | 11.30 days |

**Key Findings**

- Most valid delivered orders arrived on or before their estimated delivery dates.
- March 2018 recorded the highest monthly late-delivery rate in the analyzed period: **18.96%**.
- February 2018 also showed elevated delays at **14.13%**.
- June 2018 recorded the lowest monthly late-delivery rate: **1.16%**.

The monthly visualization covers January 2017 through August 2018.

The monthly population contains **96,184 valid orders**, while overall delivery KPIs include the valid orders from 2016.

Orders with missing actual delivery dates or inconsistent chronological sequences are excluded from these metrics without modifying the source data.

### 4.5 Delivery Performance and Customer Satisfaction

This analysis investigates whether late deliveries are associated with lower customer review scores.

Because some orders contain multiple review records, scores are averaged at the order level before comparing delivery groups.

![Delivery Performance vs Customer Satisfaction](reports/figures/delivery_vs_satisfaction.png)

**Results**

| Metric | On-Time Deliveries | Late Deliveries |
|---|---:|---:|
| Reviewed orders | 89,420 | 6,381 |
| Average review score | 4.29 / 5 | 2.27 / 5 |
| Orders with low average scores (≤ 2) | 9.22% | 62.36% |

**Key Findings**

- Late deliveries are associated with substantially lower review scores.
- The difference in average ratings is **2.02 stars**.
- Low-rating rates differ by **53.14 percentage points**.
- Low ratings are approximately **6.8 times as common** among late deliveries.

This is an observational association, not evidence that delivery delays alone cause negative customer reviews.

### Sensitivity Analysis

A separate analysis excluded orders with multiple reviews.

| Metric | On-Time Deliveries | Late Deliveries |
|---|---:|---:|
| Orders with exactly one review | 88,923 | 6,353 |
| Average review score | 4.29 | 2.27 |
| Low-rating rate | 9.24% | 62.36% |

The results remained nearly identical, suggesting that the main association is not driven primarily by orders with multiple review records.

## 5. Data Quality Findings

Data quality is treated as a core component of the project rather than an optional cleanup step.

### 5.1 Product Catalog

The product dataset contains:

- 32,951 products.
- No duplicate product IDs.
- No missing product IDs.
- 610 products without assigned categories.
- Two original categories without English translations, affecting 13 products in the source catalog.

All product IDs referenced by order items were found in the product catalog.

Missing categories are labeled `Uncategorized` in analytical outputs, while untranslated categories retain their original names.

Original source values are preserved.

### 5.2 Delivery Data

Among 96,478 orders marked as delivered:

- 8 have no actual customer delivery timestamp.
- 23 have an actual delivery timestamp earlier than the carrier handoff timestamp.
- No deliveries were found with an actual delivery timestamp earlier than the purchase timestamp.

The main delivery analysis excludes these 31 records, resulting in 96,447 valid delivered orders.

These exclusions apply to the relevant analytical metrics; records are not deleted from PostgreSQL.

### 5.3 Customer Reviews

The reviews dataset contains:

- 99,224 original review records.
- 98,673 distinct reviewed orders.
- 789 review IDs that occur more than once.
- 547 orders with multiple reviews.
- 202 orders with multiple reviews containing different scores.
- No exact duplicate rows.
- No missing review scores.
- 58,247 reviews without a written comment.

A source review identifier may occur across different orders. Therefore, the database assigns a separate internal primary key to preserve every record.

For satisfaction comparisons, review scores are aggregated to one observation per order.

### 5.4 Analytical Reconciliation

Joining delivered order items with the product catalog preserved the overall delivered-order item value:

**R$ 13,221,498.11**

Additional reconciliation confirmed:

- 96,447 valid orders in the overall delivery analysis.
- 96,184 valid orders in the January 2017–August 2018 monthly analysis.
- 95,801 valid delivered orders with at least one review in the satisfaction analysis.

These populations are intentionally different and should not be mixed without checking their definitions.

## 6. Project Structure

```text
ecommerce-intelligence/
├── data/
│   ├── raw/
│   └── processed/
├── notebooks/
├── reports/
│   └── figures/
│       ├── monthly_sales_executive.png
│       ├── top_categories.png
│       ├── monthly_delivery_performance.png
│       └── delivery_vs_satisfaction.png
├── sql/
│   ├── 01_create_tables.sql
│   ├── 02_business_kpis.sql
│   ├── 03_monthly_sales.sql
│   ├── 04_create_product_tables.sql
│   ├── 05_add_product_relationship.sql
│   ├── 06_category_performance.sql
│   ├── 07_delivery_performance.sql
│   ├── 08_monthly_delivery_performance.sql
│   ├── 09_create_reviews_table.sql
│   └── 10_delivery_vs_reviews.sql
├── src/
│   ├── business_rules.py
│   ├── explore_data.py
│   ├── investigate_anomalies.py
│   ├── load_data.py
│   ├── load_products.py
│   ├── load_reviews.py
│   ├── validate_data.py
│   ├── visualize_sales.py
│   ├── visualize_categories.py
│   ├── visualize_delivery.py
│   └── visualize_satisfaction.py
├── tests/
│   ├── test_data_quality.py
│   ├── test_delivery_rules.py
│   ├── test_load_data.py
│   └── test_load_products.py
├── README.md
└── requirements.txt
```

Raw datasets are excluded from version control.

## 7. Reproducing the Project

### Prerequisites

- Python and the dependencies listed in `requirements.txt`
- PostgreSQL
- Access to the original Olist dataset
- A configured PostgreSQL database and application user

The current scripts use the following local configuration:

| Setting | Value |
|---|---|
| Database | `ecommerce_db` |
| User | `ecommerce_user` |
| Host | `localhost` |

Database passwords are requested interactively and are not stored in source files.

### 7.1 Obtain the Dataset

Download the original dataset:

[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)

Place the original CSV files inside:

`data/raw/`

The repository does not include the source CSV files.

### 7.2 Install Python Dependencies

From the project root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 7.3 Create the Base Database Schema

After creating the PostgreSQL database and application user with the necessary permissions:

```bash
psql -h localhost -U ecommerce_user -d ecommerce_db \
  -f sql/01_create_tables.sql
```

### 7.4 Create and Load Product Tables

```bash
psql -h localhost -U ecommerce_user -d ecommerce_db \
  -f sql/04_create_product_tables.sql
```

```bash
python src/load_products.py
```

Load the product catalog before loading order items.

### 7.5 Load Customers, Orders, and Order Items

```bash
python src/load_data.py
```

The loader checks the source files and compares expected row counts with the database.

### 7.6 Apply the Product Relationship Migration

```bash
psql -h localhost -U ecommerce_user -d ecommerce_db \
  -f sql/05_add_product_relationship.sql
```

This adds the foreign key between order items and products after both datasets are available.

### 7.7 Create and Load Reviews

```bash
psql -h localhost -U ecommerce_user -d ecommerce_db \
  -f sql/09_create_reviews_table.sql
```

```bash
python src/load_reviews.py
```

This preserves original review records while using an internal database primary key.

**Important:** The setup order above describes the intended workflow. Full reconstruction from an empty database has not yet been verified by an isolated end-to-end integration test.

### 7.8 Run SQL Analyses

```bash
psql -h localhost -U ecommerce_user -d ecommerce_db \
  -f sql/02_business_kpis.sql

psql -h localhost -U ecommerce_user -d ecommerce_db \
  -f sql/03_monthly_sales.sql

psql -h localhost -U ecommerce_user -d ecommerce_db \
  -f sql/06_category_performance.sql

psql -h localhost -U ecommerce_user -d ecommerce_db \
  -f sql/07_delivery_performance.sql

psql -h localhost -U ecommerce_user -d ecommerce_db \
  -f sql/08_monthly_delivery_performance.sql

psql -h localhost -U ecommerce_user -d ecommerce_db \
  -f sql/10_delivery_vs_reviews.sql
```

### 7.9 Generate Visualizations

```bash
python src/visualize_sales.py
python src/visualize_categories.py
python src/visualize_delivery.py
python src/visualize_satisfaction.py
```

Generated charts are saved under `reports/figures/`.

### 7.10 Run Quality Checks

```bash
ruff check src/ tests/
ruff format --check src/ tests/
python -m pytest tests/ -v
```

**Current automated test status: 20 passing tests.**

The test suite covers selected data quality rules, source validation functions, and delivery date logic.

These tests do not yet provide complete end-to-end database integration coverage.

## 8. Known Limitations

- The dataset represents historical Brazilian e-commerce transactions, not current market conditions.
- Item-value metrics exclude freight and do not represent collected payments, net revenue, or profit.
- Some product categories and translations are missing.
- Some delivered orders have missing or chronologically inconsistent timestamps.
- Some review identifiers are repeated, and some orders have multiple review records.
- Delivery punctuality is assessed using calendar dates rather than exact time-of-day deadlines.
- The relationship between delivery delays and customer satisfaction is observational, not causal.
- Existing-data checks in the loaders rely primarily on record counts rather than full content reconciliation.
- The `--reload` option in `src/load_data.py` has not been updated and integration-tested for the additional `reviews` foreign-key dependency. It must not be used on the current database until this is resolved.
- The initial database setup is designed for a local PostgreSQL environment.
- An isolated, fully automated end-to-end pipeline reconstruction remains a planned improvement.

## 9. Future Development

Planned improvements include:

### Data Analytics

- Geographic order analysis
- Customer retention and cohort analysis
- Customer segmentation and RFM analysis
- Customer lifetime value estimates with explicit methodological limitations
- A consolidated executive dashboard
- Additional operational and business recommendations

### Data Engineering

- Full pipeline orchestration
- Automated database reconstruction
- Integration tests for ingestion and referential integrity
- Safer database reload workflows
- Improved content-level reconciliation and incremental loading
- Configuration management for multiple environments

## 10. Dataset Attribution

**Dataset:** Brazilian E-Commerce Public Dataset by Olist

**Source:** https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

This is an independent educational and professional portfolio project based on publicly available historical data.
