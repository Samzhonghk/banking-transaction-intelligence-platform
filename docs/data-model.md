# Data Model

## PostgreSQL schemas

| Schema | Owner | Purpose |
| --- | --- | --- |
| `ingestion` | Python ETL and Alembic | Stores source-file metadata, ETL run history, raw input records, and rejected records |
| `core` | Python application and Alembic | Stores validated and normalised banking entities and transactions |
| `risk` | Python risk pipeline and Alembic | Stores risk rules, transaction risk results, and investigation alerts |
| `analytics` | dbt | Stores dimensions, facts, and reporting marts derived from trusted core data |

## Data flow

```text
CSV / external API
        |
        v
ingestion
        |
        v
core
   |         |
   v         v
risk     analytics
         (dbt)
```

## Table catalogue

### `ingestion`

| Table | Purpose |
| --- | --- |
| `source_systems` | Defines CSV, API, and future upstream data sources |
| `source_files` | Records each received CSV file, checksum, source system, and processing status |
| `etl_runs` | Records pipeline start time, end time, status, row counts, and error summary |
| `raw_transactions` | Preserves transaction records close to their original CSV or API representation |
| `rejected_records` | Stores invalid records, rejection reasons, and the related ETL run |

### `core`

| Table | Purpose |
| --- | --- |
| `customers` | Stores validated customer identity and lifecycle information |
| `accounts` | Stores banking accounts, account type, status, currency, and opening information |
| `customer_accounts` | Represents account ownership and supports joint accounts |
| `merchants` | Stores normalised merchant identity and location information |
| `merchant_categories` | Stores merchant category codes and descriptions |
| `currencies` | Stores supported ISO currency codes and decimal precision |
| `transactions` | Stores validated banking transactions linked to accounts, merchants, and ingestion lineage |

### `risk`

| Table | Purpose |
| --- | --- |
| `risk_rules` | Stores versioned risk-rule definitions, severity, thresholds, and active status |
| `transaction_risk_results` | Stores the result, score, and evidence produced when a rule evaluates a transaction |
| `risk_alerts` | Stores investigation alerts, workflow status, assignee, outcome, and resolution timestamps |


### `analytics`

| Model | Purpose |
| --- | --- |
| `dim_dates` | Provides calendar attributes for daily, monthly, quarterly, and yearly analysis |
| `dim_customers` | Provides analytics-ready customer attributes |
| `dim_accounts` | Provides analytics-ready account attributes |
| `dim_merchants` | Provides merchant and merchant-category attributes |
| `fct_transactions` | Provides transaction measures linked to analytics dimensions |
| `mart_daily_transaction_summary` | Provides daily transaction volume, amount, failure rate, and risk totals |
| `mart_customer_risk_summary` | Provides customer-level transaction behaviour and risk indicators |