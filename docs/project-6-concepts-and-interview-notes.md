# Project 6 Concepts and Interview Notes

This document summarises the engineering concepts discussed while building
`banking-transaction-intelligence-platform`. Chinese explanations are paired
with the English terms most likely to appear in New Zealand job descriptions
and interviews.

## 1. Python project layers

Project source code uses a `src` layout:

```text
src/banking_intelligence/
├── core/
├── database/
├── ingestion/
├── transformation/
├── api/
└── observability/
```

| Directory | Responsibility |
|---|---|
| `core` | Typed settings, shared exceptions, and application-wide foundations |
| `database` | SQLAlchemy engine, sessions, metadata, and ORM models |
| `ingestion` | CSV readers, HTTP API clients, source tracking, and batch intake |
| `transformation` | pandas cleaning, type conversion, validation, and rejection logic |
| `api` | FastAPI routes, request/response schemas, and authentication |
| `observability` | Structured logging, metrics, health information, and run visibility |

These are application-code layers. They are not data warehouse layers such as
staging, DWD, or marts.

The `database` package belongs under `src/banking_intelligence` because it is
part of the installable application package. A root-level `database` directory
would become an unrelated top-level package and would not be discovered by the
current setuptools `src` configuration.

## 2. Cloud deployment and application structure

Moving the application to the cloud does not require changing its internal
Python layers. The same application package can run locally and in the cloud:

```text
Local:  FastAPI/ETL -> Docker Compose PostgreSQL
Cloud:  FastAPI/ETL container -> managed PostgreSQL
```

Environment-specific details should come from configuration:

```text
Same code + same Docker image + different configuration and resources
```

For example, local development may use `localhost`, while a cloud deployment
uses the hostname of a managed database. Secrets should be injected by the
runtime environment or a secret manager rather than embedded in the image.

### Environment options

| Pattern | Main benefit | Main trade-off |
|---|---|---|
| Development, test, and production all in cloud | Highest environment similarity and easy team sharing | Higher cost and operational complexity |
| Development/test local, production in cloud | Low cost and fast local feedback | Greater difference from production |
| Local development, ephemeral CI test, cloud production | Balanced cost, repeatability, and deployment realism | Requires both local and cloud configuration |

Project 6 uses the third pattern:

```text
Docker Compose -> local development
GitHub Actions + temporary PostgreSQL -> automated test environment
Cloud container service + managed PostgreSQL -> production
Optional cloud staging -> pre-production verification
```

## 3. Docker and Docker Compose

Docker packages an application and its runtime into an image. Docker Compose
describes how multiple containers, networks, volumes, ports, and environment
variables work together on one machine.

```text
Dockerfile -> how to build one application image
Docker -> how to run containers
compose.yaml -> which local services run together
Docker Compose -> reads compose.yaml and asks Docker to create them
```

In Project 6, Compose initially provides a reproducible local PostgreSQL
service. Later it can also start the FastAPI application and ETL task.

Compose provides basic container networking, health checks, restart policies,
volumes, and logs. Cloud platforms usually replace Compose in production with
production-grade services for scheduling, load balancing, auto-scaling,
secrets, monitoring, availability, and rollback. Docker images are still useful
as the common deployment artifact.

## 4. SQLAlchemy engine and resource cleanup

`create_engine()` creates a SQLAlchemy `Engine`, which stores the database URL
and manages a connection pool. It normally connects lazily when the application
first requests a real connection.

```python
return create_engine(
    settings.database_url,
    pool_pre_ping=True,
)
```

`pool_pre_ping=True` checks pooled connections before reuse so that stale
connections can be replaced after a database restart or network interruption.

`engine.dispose()` closes the engine's current connection pool. It does not
delete the database, tables, or data. It is useful during test cleanup and
application shutdown.

Use exception constructs according to intent:

```text
try/finally -> cleanup must happen whether the operation succeeds or fails
try/except -> a known exception has a meaningful handling strategy
try/except/finally -> handle the error and always clean up resources
```

Context managers are preferred when an API supports them:

```python
with engine.connect() as connection:
    ...
```

## 5. SQLAlchemy ORM, inheritance, and Alembic

Python inheritance uses this syntax:

```python
class Child(Parent):
    pass
```

SQLAlchemy provides `DeclarativeBase`. The project creates one shared model
base:

```python
class Base(DeclarativeBase):
    pass
```

All ORM models inherit from `Base`. Their table definitions are registered in
`Base.metadata`, which becomes the authoritative model registry used by the
application and Alembic.

```text
DeclarativeBase -> SQLAlchemy ORM foundation
Base -> Project 6 shared model base
SourceSystem/Transaction/etc. -> concrete table models
```

Alembic manages versioned PostgreSQL schema changes. It compares the desired ORM
metadata with the current database structure and generates a migration
candidate. The developer must review that migration before applying it.

```text
Git -> versions source code
uv.lock -> locks Python dependencies
Alembic revisions -> version database structure
ETL -> loads business data
```

`uv` and `pip` install Python packages; Alembic changes tables, columns, indexes,
constraints, and schemas. Alembic itself is a Python package installed through
the project's dependency manager.

Changing an ORM model does not automatically change an existing database. The
normal flow is:

```text
Change ORM model
-> generate migration
-> review migration
-> run alembic upgrade
-> verify PostgreSQL structure
```

## 6. PostgreSQL schemas and tool ownership

Project 6 separates operational and analytical ownership:

```text
PostgreSQL
├── ingestion  -> SQLAlchemy + Alembic
├── core       -> SQLAlchemy + Alembic
├── risk       -> SQLAlchemy + Alembic
└── analytics  -> dbt models
```

Typical contents:

```text
ingestion: source systems, source files, ETL runs, raw and rejected records
core: validated customers, accounts, merchants, and transactions
risk: risk rules, results, and alerts
analytics: facts, dimensions, summaries, and serving marts
```

One tool should own each relation. Alembic should not recreate dbt marts, and
dbt should not own operational tables written by the application.

Approximate warehouse terminology mapping:

| Project layer | Approximate Chinese warehouse term |
|---|---|
| ingestion/raw | ODS |
| dbt staging | staging |
| core/trusted | DWD |
| dbt intermediate | DWD processing/enrichment |
| analytics marts | DWS/ADS |

These terms are not exact one-to-one mappings. In NZ interviews, prefer the
explicit flow `raw -> staging -> trusted/core -> intermediate -> marts`, then
explain the responsibilities of each layer.

`source_system.py` defines the ORM model for
`ingestion.source_systems`. It records where a batch originated, such as a CSV
upload or HTTP API. It does not read the CSV or call the API. This metadata
supports lineage, auditing, run history, troubleshooting, and future source
expansion.

## 7. pathlib and pytest temporary paths

`Path` from `pathlib` represents a filesystem path as an object:

```python
from pathlib import Path

csv_path = Path("data") / "raw" / "transactions.csv"
```

It provides portable path joining, existence checks, directory creation, and
file operations across Windows, Linux containers, and cloud runtimes.

Pytest's `tmp_path` fixture creates a temporary directory and returns it as a
`Path` object:

```python
def test_extract_csv_preserves_raw_values(tmp_path: Path) -> None:
    ...
```

The annotation documents the fixture's real return type; it does not convert a
string into a `Path`. Temporary files keep tests isolated from project and user
data.

## 8. pandas transformation basics

This transformation strips whitespace, converts values to numbers, and writes
the result back to the column:

```python
transformed["amount"] = pd.to_numeric(
    transformed["amount"].str.strip(),
    errors="coerce",
)
```

`errors="coerce"` converts invalid values to `NaN`, allowing later validation
to quarantine invalid rows instead of stopping at the first bad value.

Parenthesised multi-line formatting improves readability and satisfies the
project line-length rule. A trailing comma makes future edits and formatting
more stable.

### DataFrame selection

`.loc` selects by row and column labels:

```python
transformed.loc[0, "transaction_id"]
```

`.iloc` selects by integer positions. `.at` and `.iat` are specialised for a
single scalar value.

The older expression below is appropriate for a list of dictionaries:

```python
records[0]["transaction_id"]
```

It is not the usual way to read the first DataFrame row because
`dataframe[0]` tries to select a column labelled `0`.

### Series and boolean masks

A pandas `Series` is one-dimensional indexed data. A boolean mask is a Series
whose values are `True` or `False`, one value per DataFrame row:

```text
10     True
20    False
30     True
dtype: bool
```

The mask can divide accepted and rejected rows:

```python
accepted = dataframe.loc[valid_mask]
rejected = dataframe.loc[~valid_mask]
```

`&`, `|`, and `~` mean element-wise AND, OR, and NOT. Validation masks use the
convention `True = valid`, so a duplicate check must be inverted:

```python
unique_id_mask = ~dataframe["transaction_id"].duplicated(keep=False)
```

`duplicated(keep=False)` marks every member of a duplicate group as `True`.
Inverting it makes unique rows `True`, ready to combine with other valid
conditions. This only detects duplicates inside the current DataFrame; a
PostgreSQL unique constraint and idempotent load logic are still required for
cross-batch protection.

## 9. Configuration-driven validation

Environment configuration and business validation configuration have different
purposes:

```text
.env -> database host, credentials, API URL, timeout, log level
validation_rules.json -> required fields, accepted statuses, supported currencies
```

A configurable rule file can contain:

```json
{
  "transactions": {
    "required_fields": ["transaction_id", "account_id", "amount"],
    "supported_currencies": ["AUD", "NZD", "USD"],
    "allowed_statuses": ["COMPLETED", "FAILED", "PENDING"]
  }
}
```

The JSON should itself be validated with a typed Pydantic model. A list of
supported currencies can be converted to a `frozenset` at runtime for fast,
immutable membership checks. Reference data that operations staff must manage
may later move to a PostgreSQL reference table.

Required-column validation compares the required and actual column sets:

```python
missing_columns = required_columns - set(dataframe.columns)
```

Missing required columns are a batch/schema failure. A present column with a
bad value is a row-level validation failure. These cases should have different
handling policies.

## 10. Rejected-record tests

Tests should verify the accepted records, the rejected source rows, and the
complete rejection reasons:

```python
assert accepted["transaction_id"].tolist() == ["TX001"]
assert rejected.index.tolist() == [1]
assert rejected.loc[1, "rejection_reason"] == (
    "missing_transaction_id;"
    "missing_account_id;"
    "invalid_amount;"
    "unsupported_currency;"
    "invalid_timestamp"
)
```

The first assertion proves only the expected transaction was accepted. The
second preserves source-row traceability. The third verifies that validation
reports every detected problem in a stable order. Adjacent strings inside
parentheses are concatenated by Python into one string.

## 11. Validation interview answer

A strong answer describes validation at several levels:

```text
Input schema validation
-> type and format standardisation
-> row-level business rules
-> accepted/rejected separation
-> database constraints
-> batch reconciliation
-> logs, metrics, and audit records
-> dbt analytical tests
```

Recommended interview answer:

> I validate data at multiple levels. I first check the input schema and typed
> configuration, then standardise values and explicitly coerce invalid types.
> I apply row-level business rules with a boolean mask and quarantine invalid
> rows with rejection reasons instead of silently dropping them. Structural
> integrity is also protected by PostgreSQL constraints. At batch level, I
> reconcile extracted, accepted, rejected, and loaded counts and record the run
> status for auditability. Analytical models add dbt tests for uniqueness,
> non-null values, relationships, and accepted values.

Fail the whole batch when the source contract is unusable, such as missing
required columns. Quarantine isolated bad rows when safe, but fail and alert if
the rejection rate exceeds an agreed threshold.

## 12. FastAPI CRUD routes

CRUD means Create, Read, Update, and Delete. A CRUD route scaffold is the
repeated FastAPI structure for endpoints such as:

```text
POST   /api/v1/customers
GET    /api/v1/customers
GET    /api/v1/customers/{customer_id}
PATCH  /api/v1/customers/{customer_id}
DELETE /api/v1/customers/{customer_id}
```

The scaffold is only the framework. Real engineering decisions include request
validation, database transaction boundaries, authentication, authorisation,
404 handling, pagination, error responses, and protection of sensitive data.
Not every banking resource should expose full CRUD; transaction records may be
read-only while authorised administrators manage risk rules.

## 13. CI, CD, and pull requests

CI (Continuous Integration) answers: "Is this change safe to merge?"

```text
Pull request
-> install locked dependencies
-> Ruff
-> unit and integration tests
-> temporary PostgreSQL
-> Alembic migration check
-> dbt tests
-> Docker image build
```

CD can mean Continuous Delivery or Continuous Deployment:

```text
Continuous Delivery -> a tested release is ready; production requires approval
Continuous Deployment -> every passing change is automatically deployed
```

A Pull Request (PR) asks to merge a development branch into `main`. It provides
a place for code review, CI status checks, discussion, and approval. Branch
protection can require successful CI checks before merging.

When a job description asks for CI/CD experience, employers usually expect more
than definitions. Junior/intermediate candidates should be able to explain or
demonstrate triggers, pipeline stages, locked dependency installation, tests,
database services, migrations, Docker builds, artifacts, secrets, environment
separation, deployment verification, approval gates, and basic rollback.

GitHub Actions, Jenkins, GitLab CI, and Azure DevOps use different syntax, but
the transferable workflow is similar:

```text
trigger -> checkout -> install -> lint -> test -> build -> publish -> deploy -> verify
```

Project 6 should use GitHub Actions for CI and initially favour Continuous
Delivery, keeping production deployment behind an approval step.

## 14. Manual SQL vs SQLAlchemy and Alembic

两种方式最终都会让 PostgreSQL 执行 DDL，例如 `CREATE TABLE`。主要区别不在
数据库最终收到什么，而在于表结构在哪里定义、数据库变更如何追踪，以及多个
环境如何保持一致。

### Execution paths

直接执行 SQL：

```text
Write CREATE TABLE SQL
-> execute it against PostgreSQL
-> manually track where and when it was executed
```

SQLAlchemy 与 Alembic：

```text
Define the SQLAlchemy ORM model
-> Alembic compares ORM metadata with the live database
-> generate and review a versioned migration
-> alembic upgrade head
-> PostgreSQL executes generated DDL
```

`SQLAlchemy ORM model` 是应用运行时使用的 Python 数据模型，也是期望表结构的
来源。`Alembic migration` 则记录数据库如何从一个版本升级到下一个版本。已经
执行并进入共享历史的 migration 不应随意重写；新的结构变化应创建新的 revision。

### Comparison

| Area | Manual SQL | SQLAlchemy + Alembic |
|---|---|---|
| Final database operation | PostgreSQL executes SQL | PostgreSQL still executes SQL |
| Schema definition | SQL files | ORM model plus migration |
| Change history | Must be managed manually | Revision chain and `alembic_version` |
| Environment consistency | Engineers must track executed scripts | Each environment runs pending revisions |
| Rollback | Requires a separate rollback script | Versioned `downgrade()` operation |
| Python application mapping | Maintained separately | ORM provides application mapping |
| Database-specific features | Direct and flexible | May require handwritten migration SQL |
| Review | Review raw DDL | Review ORM design and generated migration |

### When each approach is appropriate

Project 6 uses SQLAlchemy and Alembic for application-owned relational tables
such as `etl_runs` and `raw_transactions`. This keeps FastAPI and ETL models
aligned with development, test, CI, and production database schemas.

Direct SQL remains important and will be used for:

- dbt warehouse models and analytics transformations;
- data-quality and reconciliation queries;
- ad hoc investigation and database inspection;
- specialised PostgreSQL features such as complex indexes, partitions,
  materialised views, triggers, or bulk data migrations;
- migration operations that Alembic cannot safely infer automatically.

Autogeneration is therefore a starting point, not permission to apply database
changes blindly. An engineer must still review columns, data types, primary and
foreign keys, constraints, indexes, upgrade behaviour, and downgrade behaviour.

### Interview answer

```text
Both approaches ultimately execute SQL in PostgreSQL. For application-owned
tables, I use SQLAlchemy to define the runtime model and Alembic to create a
reviewable, versioned migration. This keeps local, CI, and production schemas
consistent and provides controlled upgrade and rollback paths. I still use
direct SQL for dbt transformations, analytics, data-quality checks, and database-
specific features that are clearer or safer to express explicitly.
```

## 15. Recent implementation questions and engineering concepts

### Python control flow and compact syntax

- `try/except` handles an error; `try/finally` guarantees cleanup whether the
  operation succeeds, fails, or returns early. Database connections and HTTP
  sessions therefore belong in `finally` cleanup or a context manager.
- A comprehension writes the produced value first and the loop second, for
  example `{row.external_account_id: row.currency_code for row in rows}`. A
  normal `for` loop is equivalent and is often clearer when the transformation
  needs several steps.
- `lambda: extract_api_transactions(...)` creates a zero-argument callable but
  does not call the API immediately. The pipeline invokes `extractor()` after it
  has created an ETL-run audit record, so extraction failures can be recorded.
- SQLAlchemy `one_or_none()` returns a complete result row or `None`.
  `scalar_one_or_none()` returns the first selected value or `None`. Both raise
  an error if more than one row is returned.

### CLI subcommands

`argparse.add_argument()` adds input to the current command. Subparsers create
separate commands, each with its own valid arguments:

```text
banking-intelligence ingest-csv <file> --source-name demo-csv
banking-intelligence ingest-api --source-name demo-api
```

This prevents CSV-only input such as `file_path` from being accepted by the API
command. The selected command determines the required source type, but CSV and
API sources remain separate rows in `ingestion.source_systems`.

### ETL runs, source systems, and lineage

One source system can have many ETL runs. `etl_runs.source_system_id` identifies
where a particular execution obtained its data. Raw, rejected, and accepted
records then retain links to that run and to their original source row.

Lineage lookup uses `(etl_run_id, source_row_number)` to locate the unique
`RawTransaction.id`. Missing or duplicate matches must fail rather than select
an arbitrary row, because an ambiguous link makes audit and replay results
unreliable.

DataFrame indexes currently map to one-based source row numbers using
`index + 1`. An explicit `source_row_number` column is safer for a mature
pipeline because filtering and index resets cannot silently destroy lineage.

### Reliable API ingestion

`requests.Session` reuses connections and centralises headers and retry policy.
The retry policy allows safe `GET` requests to retry transient HTTP status codes
such as `429`, `500`, `502`, `503`, and `504`. These are HTTP response codes, not
TCP codes. Connection and read failures are separate retry categories.

Important controls are:

- connect and read timeouts so a pipeline cannot wait forever;
- exponential backoff to avoid repeatedly attacking an unhealthy service;
- `Retry-After` support for server-side rate limiting;
- pagination so the pipeline does not silently load only the first page;
- JSON structure validation before records enter pandas or PostgreSQL;
- a maximum-page guard to stop malformed pagination from creating an infinite
  loop.

`records.extend(payload["data"])` appends every record from one response page
to the combined flat list. `append()` would instead add the page list as one
nested element.

An optional `SecretStr` API token is unwrapped only when constructing the
request header:

```text
Authorization: Bearer <token>
```

The token must not be logged. The API pipeline runs before `session.close()`;
the close operation belongs in `finally` so connections are released after
either success or failure.

### PostgreSQL bulk-insert batching

PostgreSQL's extended query protocol limits one statement to 65,535 bind
parameters. The limit is not a row-count limit. Ten thousand transaction rows
with seven bound columns require 70,000 parameters, so they cannot be sent in
one generated multi-value `INSERT`.

The loader slices `transaction_rows` into bounded batches, inserts each batch,
uses `ON CONFLICT DO NOTHING` for idempotency, and accumulates the identifiers
returned by `RETURNING`. If all batches share the caller-managed transaction, a
later failure still rolls back the complete ETL operation.

### dbt's role and warehouse modelling

dbt is not a data warehouse. PostgreSQL, Snowflake, or BigQuery stores and
computes the data; dbt organises, executes, tests, documents, and versions the
SQL transformations inside that platform. Direct SQL can perform the same
calculation, while dbt adds dependency management, environments, tests,
documentation, lineage, and repeatable CI execution.

`source()` introduces an external relation into the dbt graph. `ref()` declares
dependencies between dbt models. dbt uses those edges to build the DAG and
topologically order execution; independent branches may run concurrently.

The project materialises staging models as views because they are lightweight
source-aligned transformations. Marts are tables because they apply trusted
business rules and support repeated API, BI, and reporting queries. Staging can
technically be aggregated directly, but marts provide one consistent business
interpretation and generally faster reads.

Model grain states what one row represents. For example, a daily mart with one
row per transaction date must not contain the same date twice. If the grain is
date plus account, that column combination must be unique.

A deterministic warehouse key can be generated from the complete business key:

```sql
md5(cast(source_system_id as text) || '|' || external_account_id)
```

The delimiter prevents ambiguous concatenation, and including the source keeps
identical external IDs from different systems distinct. MD5 here creates a
stable identifier; it is not being used for password security.

dbt model YAML documents models and columns and adds tests such as `not_null`,
`unique`, and `accepted_values`. These tests detect invalid analytical data and
fail the build; unlike PostgreSQL constraints, they do not block each individual
operational write.

### dbt environments and user interfaces

One `profiles.yml` profile can define `dev`, `sit`, `uat`, and `prod` outputs.
The default `target: dev` protects normal local development, while commands such
as `dbt build --target uat` select another configured connection. Credentials
must come from environment variables or a secret manager, and production should
use a restricted service account rather than a developer credential.

dbt Core is primarily CLI- and code-driven, with generated documentation and
lineage pages. Teams that use the dbt platform also use its web UI for IDE work,
job scheduling, run history, logs, Catalog, and lineage. Other teams combine dbt
Core with VS Code, GitHub Actions, and an orchestrator UI such as Airflow.

### Hadoop and Hive learning priority for NZ/AU roles

Hadoop and Hive remain relevant in legacy enterprise estates and migration
programmes, especially in banking, telecommunications, government, and large
consultancies. Newer platforms more often separate cloud object storage from
managed compute and use Spark, Databricks, Delta Lake, Snowflake, BigQuery, or
Microsoft Fabric.

For a junior/intermediate portfolio, hands-on PySpark and Databricks skills have
higher priority than administering an on-premises Hadoop cluster. Candidates
should still explain HDFS, MapReduce, YARN, Hive tables, partitioning, the Hive
Metastore, and how these concepts carry into modern lakehouse platforms.

### API query layering and pagination trade-offs

A production API commonly separates transaction querying into four roles:

- the FastAPI route handles authentication, HTTP query parameters, status
  codes, and response construction;
- a query/service function builds and executes database queries;
- SQLAlchemy models describe operational database tables;
- Pydantic schemas define the smaller, stable public response contract.

This prevents route functions from accumulating authentication, validation,
SQL, error handling, and response conversion in one place. It also prevents
internal fields such as raw-record lineage from being exposed merely because
they were added to an ORM model.

The first transaction API version uses deterministic offset pagination:

```sql
ORDER BY transaction_timestamp DESC, id DESC
LIMIT :limit OFFSET :offset
```

Ordering by timestamp and ID makes the result stable when multiple rows share
the same timestamp. Offset pagination is straightforward for clients and is a
reasonable production choice for small and medium datasets or shallow page
navigation.

Deep offsets become increasingly expensive because PostgreSQL still has to
locate and skip preceding rows. At larger scale, the endpoint can move to
keyset (cursor) pagination:

```sql
WHERE (transaction_timestamp, id) < (:last_timestamp, :last_id)
ORDER BY transaction_timestamp DESC, id DESC
LIMIT :limit
```

Keyset pagination performs consistently for deep navigation but does not offer
arbitrary page-number jumps as naturally. Similarly, an exact `COUNT(*)` is
useful for conventional UI pagination but may become expensive on very large
tables. High-volume APIs may omit the total, cache it, calculate it
asynchronously, use an estimate, or return only `has_more` and a next cursor.

The portfolio deliberately starts with offset pagination and an exact total,
while documenting keyset pagination and count strategies as the scalability
path. Choosing the simplest design that meets current volume, and explaining
when to evolve it, reflects real engineering judgement.

### Ruff lint

`uv run ruff check .` statically checks Python code for unused imports,
incorrect import order, suspicious constructs, and configured style rules.
`uv run ruff format .` formats layout. CI runs both so inconsistent or
problematic code cannot be merged unnoticed.
