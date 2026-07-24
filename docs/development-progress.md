# Project 6 Development Progress

Project: `banking-transaction-intelligence-platform`

This document records each completed engineering step, its role in the system,
why it matters in a real project, and how the result was verified.

## Progress summary

| Status | Engineering step | Role in the project |
| --- | --- | --- |
| Done | Python `src` package structure | Separates application code from tests, documentation, and tooling |
| Done | PostgreSQL Docker Compose service | Provides a reproducible local database environment |
| Done | Typed `.env` configuration | Centralises environment-specific settings and protects secrets |
| Done | Configuration unit tests | Verifies environment loading, validation, and URL construction |
| Done | SQLAlchemy engine factory | Provides one reusable database Engine construction path |
| Done | Engine unit test | Verifies Engine type and URL configuration without a live connection |
| Done | Live PostgreSQL connection check | Proves the full application-to-database connection path |
| Done | Alembic dependency | Adds version-controlled database schema migration capability |
| Done | Alembic migration environment | Creates the standard migration structure and version directory |
| Done | Alembic application configuration | Makes migrations use the same typed settings as the application |
| Done | Shared SQLAlchemy metadata | Provides one model registry for Alembic and application code |
| Done | Alembic autogeneration metadata | Allows migrations to detect registered model changes |
| Done | PostgreSQL data-layer design | Defines schema ownership and data movement boundaries |
| Done | Data-layer table catalogue | Defines the planned operational, trusted, risk, and analytics tables |
| Done | Initial schema migration definition | Defines version-controlled PostgreSQL namespace boundaries |
| Done | Migration lifecycle verification | Applies, inspects, rolls back, and reapplies the schema revision |
| Done | First ingestion table | Introduces the first version-controlled operational data model |
| Next | ETL run audit table | Records pipeline execution status, counts, timing, and errors |

## Completed engineering steps

### 1. Python source package structure

**Completed work**

- Application code is stored under `src/banking_intelligence/`.
- Tests and engineering configuration remain outside the application package.

**Engineering role and meaning**

The `src` layout makes local development behave more like an installed package.
It prevents accidental imports from the repository root and keeps application
modules under one clear namespace. This reduces packaging differences between
local development, CI, Docker, and cloud environments.

### 2. PostgreSQL with Docker Compose

**Completed work**

- Added a PostgreSQL service managed by Docker Compose.
- Added environment-based credentials, a persistent volume, port mapping, and a
  database health check.
- Verified that the service reports `healthy`.

**Engineering role and meaning**

Docker Compose gives every developer and CI environment a repeatable database
setup. The health check provides a machine-readable readiness signal, while the
named volume prevents database data from disappearing whenever the container is
recreated.

### 3. Typed environment configuration

**Completed work**

- Added `Settings` with `pydantic-settings`.
- Loaded PostgreSQL values from `.env` and environment variables.
- Protected the password with `SecretStr`.
- Added a `database_url` property that returns a SQLAlchemy PostgreSQL URL.

**Engineering role and meaning**

Typed configuration creates one validated source of truth for local, test, CI,
Docker, and cloud environments. Secrets are kept outside source code, and
invalid or missing configuration fails early instead of causing a less clear
database error later.

**Verification**

- Unit tests verify environment-variable loading and PostgreSQL URL components.

### 4. SQLAlchemy Engine factory

**Completed work**

- Added `create_database_engine(settings)` under the database layer.
- Enabled `pool_pre_ping=True`.

**Engineering role and meaning**

The factory centralises Engine construction so ETL, API, migration, and
automation code do not each create database connections differently.
`pool_pre_ping` checks pooled connections before reuse and helps recover from
stale connections after a database restart or network interruption.

**Verification**

- The unit test confirms that the function returns an SQLAlchemy `Engine` and
  uses the URL built from the supplied settings.
- The test creates the Engine without requiring a live PostgreSQL connection.

### 5. Live application-to-PostgreSQL connection

**Completed work**

- Connected through `Settings` and `create_database_engine()`.
- Executed `SELECT current_database(), current_user`.
- Confirmed database `banking_intelligence` and user `banking_admin`.

**Engineering role and meaning**

This is an integration smoke check of the complete connection path:

```text
.env -> Settings -> SQLAlchemy URL -> Engine -> PostgreSQL
```

It proves that unit-tested configuration also works against the running service.

### 6. Alembic migration foundation

**Completed work**

- Installed Alembic as an application dependency.
- Created `alembic.ini` and the `migrations/` environment.
- Created `migrations/versions/` for versioned schema changes.

**Engineering role and meaning**

Alembic replaces ad hoc manual schema changes with repeatable, reviewable, and
reversible migration files. The same migration history can be applied in local,
CI, Docker, and cloud environments so their database structures remain aligned.

**Verification**

- Alembic version: `1.18.5`.
- Existing unit-test suite remained green after installation.

### 7. Alembic application configuration

**Completed work**

- Updated `migrations/env.py` to load the application's typed `Settings`.
- Converted the SQLAlchemy URL object into the runtime URL expected by Alembic.
- Escaped percent characters before passing the URL to Alembic's INI-backed
  configuration system.
- Kept real database credentials out of `alembic.ini` and source control.

**Engineering role and meaning**

The application and migration tool now use one configuration path instead of
maintaining separate database credentials. This reduces configuration drift
between local development, CI, Docker, and cloud deployments. A credential
change can be supplied through environment variables without editing migration
files or committing secrets.

**Verification**

- `ruff check` passed for `migrations/env.py`.
- `alembic current` connected successfully with PostgreSQL's migration dialect.
- Alembic reported transactional DDL support.
- No revision was shown because the project has not created its first migration.

### 8. Shared SQLAlchemy declarative metadata

**Completed work**

- Added `database/base.py`.
- Added a shared `Base` class derived from SQLAlchemy `DeclarativeBase`.
- Verified that `Base.metadata` is available as SQLAlchemy `MetaData`.

**Engineering role and meaning**

Every ORM model will inherit from the same `Base`, which registers its table,
columns, keys, indexes, and constraints in one metadata collection. Application
code and Alembic can therefore use the same authoritative model registry instead
of maintaining a separate schema definition.

The base class is infrastructure rather than a business table, so it does not
create a database table by itself.

**Verification**

- Ruff lint and format checks passed.
- Import verification confirmed that `Base.metadata` is `MetaData`.
- The complete unit-test suite remained green with three passing tests.

### 9. Alembic autogeneration metadata

**Completed work**

- Imported the shared SQLAlchemy `Base` into `migrations/env.py`.
- Set Alembic `target_metadata` to `Base.metadata`.

**Engineering role and meaning**

Alembic can now compare the ORM model registry with the live PostgreSQL schema.
When a registered model changes, autogeneration can produce a migration draft
for review. This removes duplicated schema definitions while still keeping every
database change explicit and version controlled.

Autogenerated migrations remain drafts: an engineer must review column types,
constraints, indexes, data migrations, and downgrade behaviour before applying
them.

**Verification**

- Ruff lint and format checks passed for `migrations/env.py`.
- `alembic check` connected to PostgreSQL and reported:
  `No new upgrade operations detected.`

### 10. PostgreSQL data layers and ownership boundaries

**Completed work**

- Defined `ingestion`, `core`, `risk`, and `analytics` PostgreSQL schemas.
- Assigned an owning implementation layer to each schema.
- Documented the high-level flow from CSV or external APIs through ingestion,
  trusted core data, risk processing, and dbt analytics.

**Engineering role and meaning**

Schema boundaries prevent ETL, application, risk, and analytics code from
writing to arbitrary tables. They establish clear ownership: Python and Alembic
manage operational structures, while dbt owns derived analytics models. This
reduces coupling and makes permissions, testing, migrations, and incident
investigation easier to reason about.

**Verification**

- `docs/data-model.md` contains the schema ownership table and data-flow diagram.
- The Markdown data-flow code fence is correctly closed.

### 11. Ingestion table catalogue

**Completed work**

- Defined `source_systems`, `source_files`, `etl_runs`, `raw_transactions`, and
  `rejected_records` under the `ingestion` schema.

**Engineering role and meaning**

The ingestion catalogue separates source identity, file receipt, pipeline
execution, raw payload preservation, and validation failures. This supports
traceability from a trusted record or rejection back to its pipeline run and
upstream source. It also allows CSV and HTTP API ingestion to share the same
operational audit model without treating raw data as trusted core data.

**Verification**

- The five tables and their responsibilities are documented in
  `docs/data-model.md`.

### 12. Core table catalogue

**Completed work**

- Defined `customers`, `accounts`, `customer_accounts`, `merchants`,
  `merchant_categories`, `currencies`, and `transactions` under the `core`
  schema.

**Engineering role and meaning**

The core catalogue provides a normalised, trusted banking model for the API,
risk processing, and dbt transformations. The `customer_accounts` junction
supports both customers with multiple accounts and joint accounts with multiple
owners. Reference entities such as currencies and merchant categories avoid
repeating inconsistent descriptive values across transaction records.

**Verification**

- The seven core tables and their responsibilities are documented in
  `docs/data-model.md`.

### 13. Risk table catalogue

**Completed work**

- Defined `risk_rules`, `transaction_risk_results`, and `risk_alerts` under the
  `risk` schema.

**Engineering role and meaning**

The risk catalogue separates versioned detection logic from the result of
evaluating an individual transaction and from the downstream investigation
workflow. This preserves evidence about which rule version produced a result,
while allowing only qualifying results to become operational alerts.

**Verification**

- The three risk tables and their responsibilities are documented in
  `docs/data-model.md`.

### 14. Analytics dbt model catalogue

**Completed work**

- Defined four dimensions, one transaction fact, and two reporting marts under
  the dbt-owned `analytics` schema.
- Completed the full catalogue with 5 ingestion tables, 7 core tables, 3 risk
  tables, and 7 analytics models.

**Engineering role and meaning**

The analytics catalogue separates dimensional reporting models from operational
tables. Dimensions provide reusable descriptive context, the transaction fact
provides measures at transaction grain, and marts provide purpose-built daily
and customer-risk outputs. dbt owns these derived models, so Alembic remains
responsible only for application-managed schemas and tables.

**Verification**

- All 22 planned tables and dbt models are documented in `docs/data-model.md`.
- Every object has an explicit layer and purpose before field-level design begins.

### 15. Initial Alembic revision scaffold

**Completed work**

- Generated revision `ca2959e45852_create_application_schemas.py`.
- Established revision `ca2959e45852` as the root of the migration history with
  `down_revision = None`.

**Engineering role and meaning**

The revision ID identifies this schema change as a node in Alembic's migration
graph. Future migrations will reference it through `down_revision`, giving every
environment the same ordered and auditable database-upgrade path.

The scaffold contains `upgrade()` and `downgrade()` functions but does not change
the database until their operations are implemented and the revision is applied.

**Verification**

- The revision file was generated under `migrations/versions/` with the expected
  message and root revision metadata.

### 16. Initial PostgreSQL schema migration definition

**Completed work**

- Implemented `upgrade()` to create `ingestion`, `core`, and `risk` schemas.
- Implemented `downgrade()` to remove the schemas in reverse order.
- Kept the dbt-owned `analytics` schema outside the Alembic migration.
- Used SQLAlchemy schema DDL objects through Alembic operations.

**Engineering role and meaning**

The migration turns logical data-layer boundaries into a version-controlled
database change. Forward and reverse operations make the change reproducible and
testable across local, CI, Docker, and cloud environments. Omitting `CASCADE`
causes rollback to fail safely if unexpected objects remain in a schema rather
than silently deleting them.

**Verification**

- Ruff lint and format checks passed for the revision.
- Upgrade and downgrade operations are symmetric and ordered in reverse.
- The complete unit-test suite remained green with three passing tests.
- The migration has not yet been applied to PostgreSQL.

### 17. Initial migration application and schema inspection

**Completed work**

- Applied revision `ca2959e45852` with `alembic upgrade head`.
- Inspected PostgreSQL schema names and owners through `psql`.
- Confirmed `core`, `ingestion`, and `risk` are owned by `banking_admin`.

**Engineering role and meaning**

Applying the migration verifies more than Python syntax: it proves that the
revision compiles to valid PostgreSQL DDL, connects with the configured role,
executes transactionally, and records the database's migration version. Direct
schema inspection confirms the intended database state rather than relying only
on a successful command exit.

**Verification**

- PostgreSQL listed `core`, `ingestion`, `public`, and `risk` schemas.
- The three application schemas have the expected owner.

### 18. Initial migration rollback verification

**Completed work**

- Rolled the database back from revision `ca2959e45852` to Alembic `base`.
- Inspected PostgreSQL after rollback.
- Confirmed that `risk`, `core`, and `ingestion` were removed and `public`
  remained.

**Engineering role and meaning**

A successful upgrade does not prove a migration is safely reversible. Testing
the downgrade while the schemas are empty confirms the rollback path before
tables and data make mistakes more costly. Direct inspection proves that the
database structure was actually removed, not merely that Alembic changed its
version marker.

**Verification**

- Alembic reported the downgrade from `ca2959e45852` to the root state.
- PostgreSQL listed only the default `public` schema after rollback.

### 19. Initial migration reapplication and head verification

**Completed work**

- Reapplied the root migration after rollback testing.
- Confirmed the database is at revision `ca2959e45852` and marked as `head`.

**Engineering role and meaning**

Reapplying the revision proves the migration is repeatable after a complete
rollback and returns the development database to the expected latest state.
Checking `alembic current` verifies that database state and migration code agree
before the next revision is created.

**Verification**

- Alembic successfully reran the schema-creation upgrade.
- `alembic current` reported `ca2959e45852 (head)`.
- The full create, inspect, rollback, inspect, and recreate lifecycle passed.

### 20. SourceSystem ORM model skeleton

**Completed work**

- Added the `database/models` package.
- Added the `SourceSystem` SQLAlchemy model.
- Mapped the class to `ingestion.source_systems`.
- Added an integer primary key.
- Added a required, length-limited, unique source name.
- Added source type, optional description, optional API base URL, active status,
  and audit timestamps.
- Added a database check constraint limiting source type to `csv` or `api`.

**Engineering role and meaning**

`SourceSystem` is the first operational model and identifies upstream providers
such as CSV feeds and HTTP APIs. Placing models in a dedicated package keeps
database mapping concerns separate from ETL, API, and configuration code. The
primary key provides stable row identity for SQLAlchemy and future foreign-key
references from files and pipeline runs.

The model also supports soft operational disablement, optional API metadata,
database-enforced source categories, and timestamp-based auditing without
storing API credentials in the table.

**Verification**

- SQLAlchemy metadata reported all eight expected columns with correct types and
  nullability, plus the named source-type check constraint.
- Ruff passed for the complete project.
- The unit-test suite remained green with three passing tests.
- No table migration has been generated yet.

### 21. Alembic model discovery for SourceSystem

**Completed work**

- Exported `SourceSystem` from the database models package.
- Loaded the models package during Alembic startup so model modules register
  their tables with shared metadata.

**Engineering role and meaning**

A model file is not automatically visible to Alembic merely because it exists.
Loading the models package ensures that all mapped tables are registered before
Alembic compares metadata with PostgreSQL. This creates one scalable discovery
path for future models instead of adding one-off migration imports everywhere.

**Verification**

- `alembic check` detected the new table `ingestion.source_systems` and listed
  its expected columns and constraints.
- The command's non-zero result was expected because a migration has not yet
  been generated for the detected table.

### 22. SourceSystem migration autogeneration and review

**Completed work**

- Autogenerated revision `2c5b9e21f71d_create_source_systems_table.py`.
- Linked it to root revision `ca2959e45852`.
- Reviewed forward and reverse operations before applying the revision.

**Engineering role and meaning**

Autogeneration converts registered ORM metadata into a migration draft, reducing
manual DDL duplication. Human review remains required because the tool cannot
understand every intended data rule, index, backfill, or rollback risk. The
review confirmed schema ownership, fields, nullability, defaults, primary key,
unique name, source-type check constraint, and table removal.

The ORM `onupdate` behaviour for `updated_at` does not appear as PostgreSQL DDL;
it runs when SQLAlchemy performs an update and is not a database trigger.

**Verification**

- Alembic reported one head: `2c5b9e21f71d`.
- Migration history is linear from `ca2959e45852` to `2c5b9e21f71d`.
- The migration has been reviewed but not yet applied.

### 23. SourceSystem migration application and live-table inspection

**Completed work**

- Applied revision `2c5b9e21f71d` to PostgreSQL.
- Created `ingestion.source_systems` with eight columns.
- Inspected the live PostgreSQL table, indexes, defaults, and constraints.

**Engineering role and meaning**

The table provides a stable registry of upstream CSV and API providers for
future ingestion runs, files, raw records, and lineage relationships. Inspecting
the live table closes the model-to-database loop and proves that ORM metadata,
autogeneration, migration review, and PostgreSQL execution agree.

**Verification**

- The primary key and generated integer sequence exist.
- Source names are protected by a unique database constraint.
- Source type is restricted to `csv` or `api` by a named check constraint.
- Active status and audit timestamps have database-side defaults.
- The complete test suite passed before the migration was applied.

### 24. EtlRun model and multi-schema Alembic discovery

**Completed work**

- Defined `ingestion.etl_runs` with source lineage, pipeline status, timestamps,
  row counters, error details, database checks, a foreign key, and an index.
- Exported `EtlRun` through the models package.
- Ensured Alembic loads the complete models package before reading metadata.
- Enabled `include_schemas=True` for online and offline Alembic contexts.

**Engineering role and meaning**

`etl_runs` provides one auditable record per pipeline execution and will support
operational monitoring, rejection-rate calculations, troubleshooting, and API
status reporting. Loading model modules is required for Alembic discovery, while
multi-schema comparison prevents false schema-drift reports outside `public`.

**Verification**

- Ruff passed for the model and migration environment.
- All three existing tests passed.
- Alembic now detects only the intended new `ingestion.etl_runs` table and its
  source-system index; the existing `source_systems` table is no longer misread.

### 25. EtlRun migration generation and review

**Completed work**

- Autogenerated revision `db015d4f3d70_create_etl_runs_table.py`.
- Confirmed the revision follows `2c5b9e21f71d` as a single migration head.
- Reviewed the table, foreign key, checks, index, defaults, schema, and rollback.
- Mechanically formatted the generated migration with Ruff.

**Engineering role and meaning**

The migration turns the reviewed ORM design into repeatable PostgreSQL DDL.
Reviewing generated migrations protects against unintended table changes and
ensures both upgrade and rollback operations preserve the intended dependency
order.

**Verification**

- Project-wide Ruff lint and format checks passed.
- All three tests passed.
- The migration has one valid parent and creates only the intended ETL audit
  table and its source lookup index.

### 26. EtlRun migration application and live inspection

**Completed work**

- Applied revision `db015d4f3d70` to PostgreSQL.
- Inspected the live `ingestion.etl_runs` table through SQLAlchemy reflection.
- Confirmed the database and ORM metadata have no outstanding migration drift.

**Engineering role and meaning**

The platform can now persist operational history for every ETL execution. The
foreign key preserves source lineage, the status constraint standardises run
states, non-negative counters protect monitoring metrics, and the source index
supports efficient history queries by upstream system.

**Verification**

- PostgreSQL contains both `ingestion.source_systems` and `ingestion.etl_runs`.
- All ten intended columns, the primary key, restricted-delete foreign key, two
  checks, and the source lookup index exist.
- The live revision is `db015d4f3d70` and `alembic check` reports no changes.

### 27. Pandas production dependency

**Completed work**

- Added pandas `3.0.3` to the application dependencies with uv.
- Updated both `pyproject.toml` and the reproducible `uv.lock` dependency graph.

**Engineering role and meaning**

Pandas will provide the tabular extraction and transformation layer for CSV
feeds. Keeping it as a locked application dependency ensures local development,
CI, Docker, and deployment environments resolve the same dependency graph.

**Verification**

- Pandas imports successfully from the project virtual environment.
- The installed version is `3.0.3` and matches the declared dependency.

### 28. Raw CSV extractor

**Completed work**

- Added the source-specific `ingestion.extractors.csv` module.
- Implemented `extract_csv()` with explicit UTF-8, malformed-row failure, raw
  string typing, and disabled automatic NA conversion.

**Engineering role and meaning**

The extractor converts a CSV source into a DataFrame while preserving raw source
values. It intentionally avoids business transformations so extraction failures
can be distinguished from validation and cleaning failures later in the pipeline.
Keeping identifiers and amounts as strings prevents lossy inference before the
platform applies explicit transformation rules.

**Verification**

- Ruff lint and format checks passed for the ingestion package.
- All three existing unit tests remained green.

### 29. Raw CSV preservation test

**Completed work**

- Added a unit test using pytest's isolated `tmp_path` fixture.
- Verified that extraction preserves leading-zero identifiers, monetary source
  text, and blank source fields without creating persistent fixture files.

**Engineering role and meaning**

The test locks down the boundary between extraction and transformation. If a
future pandas or extractor change begins inferring types or converting blanks,
the pipeline will fail early instead of silently corrupting identifiers or
changing source semantics.

**Verification**

- Project-wide Ruff lint and format checks passed.
- The full suite now contains four passing tests.

### 30. Pandas transaction transformation

**Completed work**

- Added `transform_transactions()` in the transaction transformer layer.
- Standardised identifier and description whitespace, uppercased currency,
  converted amount text to numeric values, and parsed timestamps as UTC.
- Preserved the extracted DataFrame by transforming a copy.

**Engineering role and meaning**

This transformation establishes a clear boundary between source fidelity and
standardised records. Invalid numeric or timestamp values become explicit pandas
missing values for the subsequent validation and rejected-record stage, while
the original source representation remains available for auditing.

**Verification**

- Ruff passed and all four existing tests remained green.
- A behaviour check confirmed standardised output, UTC conversion, preserved
  leading-zero account IDs, and an unchanged input DataFrame.

### 31. Transaction transformation test

**Completed work**

- Added a focused unit test for transaction standardisation.
- Verified whitespace removal, currency normalisation, numeric amount conversion,
  UTC timestamp parsing, leading-zero preservation, and input immutability.

**Engineering role and meaning**

The test defines the transformation contract independently of loading and makes
future refactoring safe. Protecting input immutability preserves the raw source
record for lineage, rejection reporting, and incident investigation.

**Verification**

- The focused transformer test passed.
- The full suite now contains five passing tests.
- Project-wide Ruff lint and format checks passed after mechanical formatting.

### 32. Base transaction validation mask

**Completed work**

- Added supported-currency rules and a vectorised transaction validity mask.
- Required transaction and account IDs, positive parsed amounts, supported
  currencies, and valid parsed timestamps.

**Engineering role and meaning**

The boolean mask turns business data-quality rules into a vectorised pandas
contract that can split accepted and rejected rows without slow row-by-row
processing. Keeping these rules outside transformation makes policy changes and
quality metrics independently testable.

**Verification**

- Ruff and all five existing tests passed.
- A mixed valid/invalid behaviour check returned `[True, False, True]`, including
  successful validation of an uppercase USD transaction.

### 33. Duplicate detection and accepted/rejected splitting

**Completed work**

- Rejected every occurrence of duplicate transaction IDs within a batch.
- Added vectorised splitting into independent accepted and rejected DataFrames.
- Preserved original DataFrame indexes for source-row lineage.

**Engineering role and meaning**

Rejecting all ambiguous duplicates prevents the pipeline from silently choosing
an authoritative financial event. Separate accepted and rejected outputs allow
valid data to continue while bad data remains observable and recoverable rather
than causing an all-or-nothing batch failure.

**Verification**

- Ruff passed and all five tests remained green.
- A mixed batch accepted one valid transaction and rejected both duplicate rows
  plus a negative-amount row while preserving source indexes `[1, 2, 3]`.

### 34. Explicit transaction rejection reasons

**Completed work**

- Added rule-specific rejection reasons for missing identifiers, duplicate IDs,
  invalid amounts, unsupported currencies, and invalid timestamps.
- Made rejection reasons the single source used to derive the valid-row mask.
- Kept the helper column only on rejected output rows.

**Engineering role and meaning**

Explicit, composable rejection reasons make bad records actionable instead of
merely excluded. A single row can retain multiple failures for remediation,
quality dashboards, and incident investigation. Deriving validity from the same
annotations prevents rule drift between filtering and error reporting.

**Verification**

- Ruff lint and format checks passed and all five tests remained green.
- A mixed batch produced one accepted row, one duplicate-only rejection, and one
  rejection containing five ordered failure reasons.

### 35. Accepted/rejected validation test

**Completed work**

- Added a validator test with one accepted record and one multi-failure rejected
  record.
- Verified stable rejection reason ordering and original source-row index lineage.

**Engineering role and meaning**

This test protects the partial-success ingestion design: valid records continue,
while invalid records retain enough context to explain and remediate every failed
rule. It also fixes the rejection reason contract consumed by future database
loading, monitoring, and APIs.

**Verification**

- The focused validator test passed.
- The full suite now contains six passing tests.
- Project-wide Ruff checks passed and Alembic reports no schema drift.

### 36. CI baseline commit

**Completed work**

- Re-ran local quality checks and staged the PostgreSQL, Alembic, pandas ETL,
  tests, dependency lock, and documentation baseline.
- Audited staged paths for secrets, virtual environments, caches, and test temp
  directories before committing.
- Created commit `cbd38c6` (`feat: add PostgreSQL and pandas ingestion foundation`).

**Engineering role and meaning**

A clean, tested baseline gives the first CI workflow a known local result to
reproduce. Reviewing staged content before commit prevents credentials and local
runtime artefacts from becoming part of repository history.

**Verification**

- The commit was created successfully.
- The working tree was clean immediately after the baseline commit.

### 37. GitHub repository publication

**Completed work**

- Created the public GitHub repository without generating a competing history.
- Renamed the local default branch to `main`, configured `origin`, and performed
  the first push with upstream tracking.

**Engineering role and meaning**

Publishing a clean baseline provides the remote event source and execution
context required by GitHub Actions. Upstream branch tracking keeps future local
commits and CI-triggering pushes explicit and predictable.

**Verification**

- Local `main` and `origin/main` both point to commit `cbd38c6`.
- Fetch and push URLs target the intended portfolio repository.

### 38. GitHub Actions trigger contract

**Completed work**

- Created `.github/workflows/ci.yml` in the GitHub Actions discovery path.
- Configured execution for pushes to `main`, pull requests targeting `main`, and
  manual workflow dispatch.

**Engineering role and meaning**

The trigger contract defines when repository changes must pass automated quality
checks. Push checks protect the shared branch, pull-request checks provide review
feedback before merge, and manual dispatch supports controlled re-runs.

**Verification**

- The workflow exists at the exact repository path required by GitHub.
- Both branch filters target the published `main` branch.

### 39. First learner-owned Python quality CI workflow

**Completed work**

- Added a least-privilege `quality` job running on GitHub-hosted Ubuntu.
- Configured repository checkout, pinned `uv` setup with dependency caching,
  project Python installation, and locked development dependency sync.
- Added Ruff lint, Ruff formatting verification, and the full pytest suite as
  required quality gates.
- Committed and pushed the learner-written workflow to `main`.

**Engineering role and meaning**

This workflow moves quality checks from a developer's local machine into a
repeatable clean environment. Every push and pull request now proves that the
locked dependencies can be installed and that the code satisfies the same lint,
formatting, and regression-test contract before further delivery work begins.
Pinning the third-party setup action by commit SHA also reduces supply-chain
risk, while read-only repository permissions apply least privilege.

**Verification**

- GitHub Actions workflow run `CI #1` completed successfully on `main` for
  commit `7ea911e`.
- The remote job completed dependency installation, Ruff lint, Ruff formatting
  verification, and pytest without a failing step.
- Local Ruff lint and formatting verification also passed.

### 40. Raw transaction ingestion model

**Completed work**

- Added the `ingestion.raw_transactions` SQLAlchemy model at one row per source
  record received by an ETL run.
- Added lineage through `etl_run_id` and `source_row_number`.
- Added PostgreSQL JSONB storage for the unmodified source payload.
- Added a SHA-256-sized record fingerprint field and a run-scoped uniqueness
  constraint for ingestion idempotency.
- Enforced one stored record per source row within each ETL run.
- Registered the model so Alembic can discover it through shared metadata.

**Engineering role and meaning**

Keeping an immutable raw layer separates source evidence from changing business
rules. Transactions can be revalidated or transformed later without rereading
the original file or API, while run lineage and fingerprints support auditing,
incident investigation, and controlled retry behaviour.

**Verification**

- Ruff lint and formatting checks passed for all database models.
- Importing the model package registered `ingestion.raw_transactions` in
  SQLAlchemy metadata.
- No migration was generated or applied in this step; database state is
  intentionally unchanged pending migration review.

### 41. Raw transaction migration generation and review

**Completed work**

- Autogenerated revision `8db49e4892cf` for
  `ingestion.raw_transactions` against the live PostgreSQL schema.
- Reviewed the generated JSONB column, ETL run foreign key, positive row-number
  check, run-scoped uniqueness constraints, and lookup indexes.
- Confirmed that `downgrade()` removes the indexes and table without affecting
  the parent ETL run table.
- Applied Ruff's mechanical migration-template fixes and formatting.

**Engineering role and meaning**

The revision turns an application model change into a versioned database change
that can be reviewed, reproduced, rolled back, and applied consistently in local,
CI, and cloud environments. Reviewing generated DDL prevents ORM mistakes from
being applied blindly to shared databases.

**Verification**

- Alembic detected only the intended new table and its two indexes.
- The migration file passes Ruff lint and formatting checks.
- The revision has not yet been applied; PostgreSQL remains at the previous
  revision until the upgrade step is explicitly run.

### 42. Raw transaction migration application and inspection

**Completed work**

- Applied revision `8db49e4892cf` to the local PostgreSQL database.
- Confirmed Alembic reports the revision as the current head.
- Inspected the physical `ingestion.raw_transactions` relation with `psql`.

**Engineering role and meaning**

Applying and inspecting the revision proves that the versioned schema definition
can be executed by PostgreSQL and produces the intended physical design. This
closes the gap between an ORM declaration, generated migration code, and the
database objects that loaders will actually use.

**Verification**

- PostgreSQL contains the expected integer, JSONB, fingerprint, and timezone-aware
  timestamp columns with the intended nullability and defaults.
- The primary key, ETL run and fingerprint indexes, and both run-scoped unique
  constraints are present.
- Alembic reports `8db49e4892cf (head)`.

### 43. Deterministic raw-record fingerprinting

**Completed work**

- Added `build_record_fingerprint()` using canonical JSON serialisation and
  SHA-256.
- Normalised dictionary key order and JSON separators before hashing while
  preserving Unicode through UTF-8 encoding.
- Added a unit test covering field-order independence, content sensitivity, and
  the expected 64-character digest length.

**Engineering role and meaning**

A stable fingerprint gives the ingestion layer a reproducible technical identity
when an upstream record has no trustworthy event ID. It supports duplicate
detection and safe retries without relying on Python's process-dependent
`hash()` implementation. Business-level uniqueness will still be enforced later
using transaction identifiers in the trusted core layer.

**Verification**

- The focused fingerprint test passed.
- Ruff lint passed and both files were formatted.

### 44. Raw duplicate-preservation constraint correction

**Completed work**

- Refined the raw-layer grain after designing the loader: identical payloads at
  different source rows must remain observable as separate raw records.
- Removed the run-plus-fingerprint uniqueness rule from ORM metadata while
  retaining the fingerprint lookup index.
- Kept run-plus-source-row uniqueness as the ingestion retry boundary.
- Generated and reviewed corrective revision `7005ac6097cb` without rewriting
  the already-applied historical revision.

**Engineering role and meaning**

An immutable raw layer should preserve what the source actually delivered,
including duplicate rows, so downstream validation can reject and report them.
Source-position uniqueness prevents the same run and row from being inserted
twice, while fingerprints remain useful for comparison without discarding raw
evidence. Creating a new revision also preserves trustworthy migration history.

**Verification**

- Alembic detected only removal of
  `uq_raw_transactions_run_fingerprint`.
- The corrective migration retains other constraints and indexes and includes a
  reversible downgrade.
- Ruff checks passed; the corrective revision has not yet been applied.

### 45. Raw duplicate-preservation migration application

**Completed work**

- Applied corrective revision `7005ac6097cb` to PostgreSQL.
- Confirmed Alembic reports the corrective revision as the current head.
- Inspected live PostgreSQL unique constraints through SQLAlchemy reflection.

**Engineering role and meaning**

The applied constraint model now matches raw-layer responsibilities: every source
position is stored at most once per run, but identical payloads from different
positions remain available for downstream duplicate validation and audit.

**Verification**

- The only non-primary unique constraint on `raw_transactions` is
  `uq_raw_transactions_run_source_row` over `etl_run_id` and
  `source_row_number`.
- No run-plus-fingerprint unique constraint remains in PostgreSQL.
- Alembic reports `7005ac6097cb (head)`.

### 46. Raw transaction bulk-loader unit contract

**Completed work**

- Added a caller-transaction-aware loader that converts raw DataFrame records
  into lineage-aware `raw_transactions` insert mappings.
- Added logical source positions, original JSON payloads, and deterministic
  fingerprints to every prepared row.
- Used one SQLAlchemy execute call for batch insertion and returned the loaded
  row count.
- Added a mock-based unit test that verifies the target table, prepared values,
  row ordering, fingerprint, and single bulk execute call.
- Added an empty-input boundary test that returns zero without issuing SQL.

**Engineering role and meaning**

The loader keeps database transaction ownership in the pipeline layer, allowing
raw inserts and ETL audit updates to commit or roll back together. A two-record
unit test also exposed and prevented an early-return indentation bug that a
single-record test would not have detected.

**Verification**

- Both focused loader unit tests passed, covering multi-row and empty inputs.
- Ruff lint and formatting checks passed for the loader and test.
- No real database is used by this unit test; PostgreSQL behaviour remains an
  explicit integration-test responsibility.

### 47. Raw transaction PostgreSQL integration test

**Completed work**

- Added a reusable integration-test connection fixture backed by real
  PostgreSQL.
- Wrapped every integration test in a caller-managed transaction that is rolled
  back during fixture cleanup.
- Added an integration test that creates source and ETL run lineage, loads two
  identical raw payloads, queries the stored JSONB rows, and compares their
  fingerprints.

**Engineering role and meaning**

The integration layer verifies behaviour that mocks cannot prove: PostgreSQL
connectivity, foreign keys, JSONB adaptation, generated SQL, live constraints,
and transaction cleanup. Preserving two identical payloads at distinct source
positions confirms that raw evidence is retained for downstream duplicate
validation.

**Verification**

- The real PostgreSQL loader integration test passed.
- Both duplicate payloads were stored at source positions 1 and 2 with identical
  fingerprints.
- The fixture rolled the transaction back after the test.
- Ruff lint and formatting checks passed for the loader, fixture, and test.

### 48. PostgreSQL integration CI preparation

**Completed work**

- Added a temporary PostgreSQL service to the GitHub Actions quality job.
- Added test-only database connection environment variables and a PostgreSQL
  health check.
- Added an Alembic upgrade step before pytest so every CI run builds its schema
  from versioned migrations.
- Resolved duplicate unit/integration test module names and removed an accidental
  duplicate loader implementation from the package initializer.

**Engineering role and meaning**

The CI job can now validate migrations and database integration in a fresh,
disposable PostgreSQL environment instead of depending on a developer's local
database. Building the schema from zero also proves that migration history is
complete and deployable.

**Verification**

- The complete local suite contains ten passing tests, including the PostgreSQL
  integration test.
- Repository-wide Ruff lint and formatting checks passed.
- `alembic check` reported no new upgrade operations.
- Remote GitHub Actions verification remains pending until the changes are
  committed and pushed.

## Delivery and learning split

To keep the portfolio moving while preserving intermediate Data Engineer skills,
future tasks use two ownership tracks.

**Learner-owned core work**

- Write the important pandas transformations, validation rules, ETL control flow,
  SQL analysis, data-quality queries, and selected unit tests.
- Build the GitHub Actions CI/CD workflow, including triggers, dependency setup,
  Ruff, pytest, Docker image build, deployment stages, and failure diagnosis.
- Make data-model decisions and explain keys, constraints, grain, idempotency,
  rejection handling, and incremental loading.
- Run and interpret migrations, tests, lint checks, Docker services, and pipeline
  failures.

**Codex-assisted engineering work**

- Scaffold repetitive SQLAlchemy models, Alembic boilerplate, package exports,
  configuration wiring, Docker files, API CRUD boilerplate,
  logging setup, and documentation.
- Run repository-wide checks, review generated migrations, diagnose errors, and
  maintain the progress records.
- The learner reviews these changes and must be able to explain their purpose,
  but does not need to type every line manually.

Every future task will be labelled `需要手敲`, `可以复制但需要理解`,
`由 Codex 完成并由你 review`, or `运行命令即可`.

CI/CD is learner-owned: Codex explains requirements and reviews the workflow but
does not write the workflow on the learner's behalf.

## Current step

Commit and push the raw ingestion and PostgreSQL CI milestone, then verify the
remote GitHub Actions run before continuing to rejected-record persistence.
