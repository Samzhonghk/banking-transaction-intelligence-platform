# Data Engineer Technical Interview Questions and Answers

面向 New Zealand Junior / Intermediate Data Engineer 求职的中英双语面试题库。

> 使用原则：这些答案是表达模板，不是背诵稿。只描述自己真正完成、理解或正在实现的内容。尚未在生产环境使用过的工具，应明确说明学习阶段和当前实践范围。

## Contents

1. [Interview strategy](#interview-strategy)
2. [Introduction and project deep dive](#introduction-and-project-deep-dive)
3. [ETL and pipeline reliability](#etl-and-pipeline-reliability)
4. [SQL and PostgreSQL](#sql-and-postgresql)
5. [Python data engineering](#python-data-engineering)
6. [Data modelling and warehousing](#data-modelling-and-warehousing)
7. [dbt, Airflow, Docker, and CI/CD](#dbt-airflow-docker-and-cicd)
8. [Monitoring, cloud, and behavioural questions](#monitoring-cloud-and-behavioural-questions)

## Interview strategy

技术问题建议使用以下结构回答：

```text
Definition
→ Why it matters
→ Practical implementation
→ Example
→ Trade-off or limitation
```

项目题建议使用：

```text
Problem
→ Architecture
→ My responsibility
→ Key engineering decision
→ Testing and result
→ Next improvement
```

行为题使用 STAR：

```text
Situation
Task
Action
Result
```

英文回答建议控制在 30–90 秒。遇到不确定的问题，先澄清假设，再解释思路，不要直接猜答案。

---

## Introduction and project deep dive

### 1. 请介绍一下你自己

**English question:** Tell me about yourself.

**中文参考答案：**

我正在向 Data Engineer 和 Software Engineer 方向发展，主要使用 Python、SQL、PostgreSQL、FastAPI 和 Docker。我已经完成了 SQL 分析、Python ETL 和查询 API 项目，目前正在构建一个银行交易数据平台，重点实践数据质量、幂等导入、数据库迁移、数据建模、测试和 CI/CD。我希望进入 junior 或 intermediate 岗位，在真实团队中继续提高 pipeline reliability、cloud deployment 和 stakeholder communication 能力。

**English answer:**

I’m developing towards Data Engineering and Software Engineering roles, mainly using Python, SQL, PostgreSQL, FastAPI, and Docker. I’ve completed projects involving SQL analysis, Python ETL, and query APIs, and I’m currently building a banking transaction intelligence platform focused on data quality, idempotent ingestion, database migrations, data modelling, testing, and CI/CD. I’m looking for a junior or intermediate role where I can contribute to reliable data pipelines and continue developing my cloud and stakeholder communication skills.

**Possible follow-ups:**

- Why did you choose Data Engineering?
- Which project are you most proud of?
- Which area do you want to improve next?

### 2. 请介绍你的银行交易数据平台

**English question:** Can you walk me through your banking transaction platform?

**中文参考答案：**

这个项目的目标是构建一条可追踪、可测试、可重跑的数据链路。CSV 或其他源数据先进入 ingestion 层，Python 负责解析、类型转换和基础业务校验。合法数据进入 PostgreSQL，非法记录保存原始内容和拒绝原因。每次运行记录 run ID、文件 checksum、开始结束时间、接受与拒绝数量。后续由 dbt 构建 staging、fact、dimension 和 marts，FastAPI 提供交易查询、汇总和风险接口。Docker Compose 负责本地环境，GitHub Actions 负责 lint、测试、migration 检查和 image build。

**English answer:**

The project is designed as a traceable, testable, and safely rerunnable data platform. CSV or other source data enters an ingestion layer, where Python handles parsing, type conversion, and initial business validation. Valid records are loaded into PostgreSQL, while rejected records retain the original payload and rejection reason. Each run records a run ID, file checksum, timestamps, and accepted and rejected counts. dbt will build staging models, facts, dimensions, and marts, while FastAPI exposes transaction, summary, and risk endpoints. Docker Compose provides the local environment, and GitHub Actions will run linting, tests, migration checks, and container builds.

**Key interview point:**

明确区分已经完成的部分和仍在实现的部分。可以说 “I have completed…” 或 “I am currently implementing…”，不要把计划描述成生产经验。

### 3. 为什么选择 PostgreSQL，而不是继续使用 SQLite？

**English question:** Why did you choose PostgreSQL instead of SQLite?

**中文参考答案：**

SQLite 非常适合学习、单机分析和轻量应用，但这个项目需要更接近生产环境的并发连接、权限管理、网络访问、连接池、JSON、约束和查询优化能力。PostgreSQL 还可以支持 API、ETL、dbt 和集成测试同时访问数据库。代价是本地环境、migration 和运维复杂度更高，因此我使用 Docker Compose 提供可重复的开发环境。

**English answer:**

SQLite is excellent for learning, local analysis, and lightweight applications, but this project needs production-oriented capabilities such as concurrent connections, role management, network access, connection pooling, richer data types, constraints, and query optimisation. PostgreSQL also supports the API, ETL process, dbt, and integration tests accessing the database as separate clients. The trade-off is greater setup and operational complexity, which I manage locally with Docker Compose.

---

## ETL and pipeline reliability

### 4. ETL 和 ELT 有什么区别？

**English question:** What is the difference between ETL and ELT?

**中文参考答案：**

ETL 是 Extract、Transform、Load，即先在数据库外转换数据，再加载目标系统。ELT 是 Extract、Load、Transform，即先保留原始数据，再利用数据库或数仓完成转换。ETL 适合加载前必须严格清洗的场景；ELT 适合 Snowflake、BigQuery 等计算能力较强的现代数仓。实际工程经常混合使用，例如 Python 负责文件解析和基础校验，dbt 在 PostgreSQL 或云数仓中完成分析模型转换。

**English answer:**

ETL means extract, transform, and then load, so transformations happen before data reaches the target system. ELT means extract, load, and then transform, so raw data is retained and transformations run inside the database or warehouse. ETL is useful when data must be strictly cleaned before loading, while ELT works well with scalable analytical platforms. In practice, I can use Python for parsing and initial validation, then use dbt for transformations inside PostgreSQL or a cloud warehouse.

### 5. 什么是幂等 ETL？

**English question:** What does idempotency mean in a data pipeline?

**中文参考答案：**

幂等表示相同输入被处理一次或多次，最终结果保持一致，不会产生失控的重复记录。实现时首先要定义业务唯一键，例如 source transaction ID。然后可以结合文件 checksum、unique constraint、upsert 和 ETL run log。数据库约束是最后防线，应用逻辑负责给出更清楚的处理结果。需要注意，幂等不一定意味着忽略所有重复，也可能将重复文件标记为 skipped，并保留审计记录。

**English answer:**

Idempotency means processing the same input once or multiple times produces the same final state instead of uncontrolled duplicates. I first define a business key, such as the source transaction ID, then combine file checksums, unique constraints, upserts, and ETL run logs. Database constraints provide the final safeguard, while application logic records a clear outcome. Idempotency does not always mean silently ignoring duplicates; a repeated file can be marked as skipped while still being audited.

**Possible follow-ups:**

- What if the source has no transaction ID?
- When would you use insert, upsert, or delete-and-reload?
- How would you handle a corrected source file with the same name?

### 6. Pipeline 执行一半失败怎么办？

**English question:** What would you do if a pipeline failed halfway through?

**中文参考答案：**

我会先确定失败边界和写入策略。一个数据库批次内的相关写入应放入 transaction，失败时回滚，避免半完成状态。整个 run 要记录 running、failed 或 completed 状态以及失败阶段。重跑前要依靠幂等键判断已经提交的批次。对于大文件，不一定把整份文件放进一个巨大 transaction，而可以采用可审计的小批次和 checkpoint，在一致性、锁时间和重跑成本之间权衡。

**English answer:**

I would first define the failure boundary and commit strategy. Related writes within a database batch should be transactional so they roll back together and do not leave a partial state. The overall run should record a status such as running, failed, or completed, together with the failed stage. On rerun, idempotency keys determine which committed batches already exist. For very large files, I may use auditable smaller batches and checkpoints rather than one huge transaction, balancing consistency, lock duration, and rerun cost.

### 7. 哪些错误应该重试？

**English question:** Which pipeline failures should be retried?

**中文参考答案：**

临时性错误适合有限重试，例如短暂网络故障、数据库连接超时或服务限流。数据格式错误、缺失必填字段和违反业务规则通常不应该重试，因为相同输入不会自动变正确，应该进入 rejected records。配置错误或认证失败需要人工修复。重试应有次数上限、backoff 和告警，避免无限循环。

**English answer:**

Transient failures are appropriate for limited retries, such as temporary network issues, database timeouts, or service rate limits. Invalid data, missing required fields, and business-rule violations should normally not be retried because the same input will not become valid; those records should be rejected with a reason. Configuration and authentication failures usually require intervention. Retries should have limits, backoff, and alerting to prevent infinite loops.

### 8. 如何保证数据质量？

**English question:** How do you ensure data quality?

**中文参考答案：**

我会从 completeness、validity、uniqueness、referential integrity、timeliness 和 reconciliation 六个方面设计检查。例如交易 ID 必须唯一，金额必须能够转换成 `NUMERIC`，账户外键必须存在，货币代码必须来自允许集合，每日文件必须按时到达，加载后的记录数需要与源数据对账。校验要分层：Python 负责解析和业务校验，PostgreSQL 使用 `NOT NULL`、`UNIQUE`、`CHECK` 和 foreign key，dbt 对分析模型执行 tests，监控系统观察 freshness 和数量异常。

**English answer:**

I design checks around completeness, validity, uniqueness, referential integrity, timeliness, and reconciliation. For example, transaction IDs must be unique, amounts must convert safely to `NUMERIC`, referenced accounts must exist, currency codes must be accepted, daily files must arrive on time, and loaded counts should reconcile with the source. Quality controls should be layered: Python handles parsing and business validation, PostgreSQL enforces constraints, dbt tests analytical models, and monitoring checks freshness and volume anomalies.

### 9. 如何处理 rejected records？

**English question:** How would you handle rejected records?

**中文参考答案：**

被拒绝的数据不应被静默丢弃。我会保存 run ID、source file、row number、原始 payload、错误代码、错误信息和 rejected timestamp。这样能够统计错误类型、定位源系统问题并在修复后重处理。日志只用于观察运行过程，而 rejected table 或受控文件用于可查询的业务审计。敏感字段还需要脱敏和访问控制。

**English answer:**

Rejected data should not be silently discarded. I would retain the run ID, source file, row number, original payload, error code, error message, and rejection timestamp. This supports error analysis, source-system investigation, and controlled reprocessing after correction. Logs are useful for operational events, while a rejected-record store provides queryable audit data. Sensitive fields should also be masked and access-controlled.

---

## SQL and PostgreSQL

### 10. INNER JOIN 和 LEFT JOIN 有什么区别？

**English question:** What is the difference between an INNER JOIN and a LEFT JOIN?

**中文参考答案：**

`INNER JOIN` 只返回两边都匹配的记录。`LEFT JOIN` 保留左表全部记录，右表没有匹配时返回 `NULL`。例如统计所有客户，包括没有交易的客户，应从 customers 出发 LEFT JOIN transactions。如果只关心发生过交易的客户，则可以使用 INNER JOIN。选择 join 类型应由业务问题决定。

**English answer:**

An `INNER JOIN` returns only rows that match on both sides. A `LEFT JOIN` preserves every row from the left table and returns `NULL` for unmatched right-side values. To report all customers including those without transactions, I would start from customers and left join transactions. If I only need customers who have transacted, an inner join may be appropriate. The business requirement determines the join type.

### 11. GROUP BY 和 window function 有什么区别？

**English question:** What is the difference between GROUP BY and a window function?

**中文参考答案：**

`GROUP BY` 将多行聚合成每个 group 一行；window function 保留原始行，同时计算排名、累计值或组内统计。例如客户总交易金额可以使用 `GROUP BY customer_id`。如果要显示每笔交易，并同时显示客户累计金额，则可以使用 `SUM(amount) OVER (PARTITION BY customer_id ORDER BY transaction_time)`。

**English answer:**

`GROUP BY` collapses multiple rows into one result row per group. A window function preserves the original rows while calculating ranks, running totals, or group-level metrics. Total transaction value per customer can use `GROUP BY customer_id`. To show every transaction together with a customer’s running total, I could use `SUM(amount) OVER (PARTITION BY customer_id ORDER BY transaction_time)`.

### 12. 如何使用 SQL 去重？

**English question:** How would you remove duplicate rows using SQL?

**中文参考答案：**

首先定义业务上的重复，然后使用 `ROW_NUMBER()` 按业务键分组，并根据更新时间或数据可信度排序。保留 `row_number = 1` 的记录，其余为重复。长期方案不是每天依赖清理 SQL，而是在 ingestion 和数据库层使用 business key 与 unique constraint 防止新重复进入。

```sql
WITH ranked AS (
    SELECT
        transaction_id,
        updated_at,
        ROW_NUMBER() OVER (
            PARTITION BY source_transaction_id
            ORDER BY updated_at DESC
        ) AS row_number
    FROM transactions
)
SELECT *
FROM ranked
WHERE row_number = 1;
```

**English answer:**

I first define duplicates in business terms, then use `ROW_NUMBER()` partitioned by the business key and ordered by update time or source reliability. The row with number one is retained and the remaining rows are duplicates. The long-term solution should also prevent new duplicates through ingestion logic and a database unique constraint rather than relying only on cleanup queries.

### 13. SQL 查询很慢时如何排查？

**English question:** How would you investigate a slow SQL query?

**中文参考答案：**

我会先确认实际慢查询、参数和数据量，再使用 `EXPLAIN ANALYZE` 查看执行计划。重点检查 sequential scan、join strategy、过滤选择性、估算行数与实际行数、排序和返回数据量。然后评估索引、查询重写、预聚合或 pagination。任何优化都要在相同条件下重新测量，不能只凭感觉添加索引。

**English answer:**

I would first identify the actual slow query, parameters, and data volume, then inspect the execution plan with `EXPLAIN ANALYZE`. I would look for sequential scans, join strategies, filter selectivity, estimated versus actual row counts, sorting, and excessive result volume. I would then consider indexes, query rewrites, pre-aggregation, or pagination. Every optimisation should be measured again under comparable conditions rather than assuming an index will help.

### 14. Index 有什么作用和代价？

**English question:** What are the benefits and costs of a database index?

**中文参考答案：**

索引可以减少查询需要扫描的数据，常用于过滤、join、排序和唯一性约束。但索引会占用存储空间，并增加 insert、update 和 delete 的维护成本。低选择性字段或经常变化但很少查询的字段不一定适合单独索引。应根据真实查询模式和执行计划设计复合索引的列顺序。

**English answer:**

An index can reduce the amount of data scanned for filtering, joins, ordering, and uniqueness enforcement. The trade-offs are additional storage and extra work on inserts, updates, and deletes. A low-selectivity column or a frequently updated column that is rarely queried may not benefit from its own index. Composite index order should be based on real query patterns and execution plans.

### 15. 什么是数据库 transaction？

**English question:** What is a database transaction, and why is it important?

**中文参考答案：**

Transaction 将一组相关数据库操作视为一个工作单元，要么全部提交，要么失败后回滚。例如 ETL 插入交易、更新 run status 和统计数量时，如果中间失败，不应留下彼此不一致的状态。Transaction 能保护原子性和一致性，但过大的 transaction 会增加锁时间、WAL 和回滚成本，因此需要合理选择边界。

**English answer:**

A transaction treats related database operations as one unit of work, so they either commit together or roll back on failure. For example, inserting transactions, updating a run status, and recording counts should not leave inconsistent partial results. Transactions protect atomicity and consistency, but very large transactions can increase lock duration, write-ahead logging, and rollback cost, so the boundary should be chosen carefully.

### 16. 为什么金额不使用 float？

**English question:** Why should financial amounts not normally use floating-point types?

**中文参考答案：**

二进制浮点数不能精确表示很多十进制金额，连续计算可能产生舍入误差。银行金额通常使用 PostgreSQL `NUMERIC(precision, scale)`，Python 中使用 `Decimal`。同时还要明确货币代码、舍入规则和允许的小数位数，不能只选择数据类型而忽略业务定义。

**English answer:**

Binary floating-point values cannot exactly represent many decimal amounts, so repeated calculations can introduce rounding errors. Financial values are normally stored with PostgreSQL `NUMERIC(precision, scale)` and handled with Python `Decimal`. The design must also define currency, rounding rules, and allowed decimal places rather than relying only on the data type.

---

## Python data engineering

### 17. Python 如何处理大文件？

**English question:** How would you process a large file in Python?

**中文参考答案：**

我不会默认把整个文件加载进内存，而会使用 iterator、generator 或分块读取。每条或每批数据完成解析和校验后，再通过 PostgreSQL COPY 或 batch insert 写入。批次大小需要测量，因为太小会增加往返开销，太大则增加内存和回滚成本。还应记录处理进度、拒绝数量和 checkpoint。

**English answer:**

I would avoid loading the whole file into memory by default and use iterators, generators, or chunked reads. After parsing and validating each record or batch, I could load data using PostgreSQL `COPY` or batch inserts. Batch size should be measured because very small batches increase round trips, while very large batches increase memory and rollback cost. I would also record progress, rejection counts, and checkpoints.

### 18. 为什么要将 ETL 拆成多个函数？

**English question:** Why would you separate an ETL pipeline into multiple functions or components?

**中文参考答案：**

Extract、parse、validate、transform 和 load 的失败方式、输入输出和测试需求不同。拆分后可以单独测试纯转换逻辑，替换数据来源或目标数据库，也能更清楚地定位失败阶段。但拆分不能变成过度抽象，每个函数应有明确责任和稳定接口，而不是为了文件数量而拆分。

**English answer:**

Extraction, parsing, validation, transformation, and loading have different failure modes, inputs, outputs, and testing needs. Separating them allows pure transformations to be unit tested, sources or destinations to be replaced, and failed stages to be identified clearly. However, separation should not become unnecessary abstraction; each function should have a clear responsibility and useful interface.

### 19. Data pipeline 应该测试什么？

**English question:** What would you test in a data pipeline?

**中文参考答案：**

单元测试覆盖解析、类型转换、业务校验和错误分类；数据库集成测试覆盖约束、transaction、repository 和真实 PostgreSQL 行为；端到端测试覆盖从输入文件到目标表及审计记录的完整流程。关键场景包括空文件、缺失列、错误日期、重复记录、数据库失败、回滚和相同输入重跑。测试必须隔离，不能连接开发或生产数据库。

**English answer:**

Unit tests should cover parsing, type conversion, business validation, and error classification. Database integration tests should cover constraints, transactions, repositories, and real PostgreSQL behaviour. End-to-end tests should verify the complete flow from source input to target tables and audit records. Important cases include empty files, missing columns, invalid dates, duplicates, database failures, rollback, and rerunning the same input. Tests must be isolated from development and production databases.

### 20. 如何处理异常而不隐藏错误？

**English question:** How do you handle exceptions without hiding failures?

**中文参考答案：**

我会只捕获能够有意义处理的具体异常，而不是使用空的 `except Exception` 后继续运行。数据级异常可以转换成 rejected record；暂时性基础设施异常可以记录上下文后重试；未知或不可恢复异常应记录 run ID 和 stage 后重新抛出，使任务失败。日志需要包含上下文，但不能输出密码或敏感数据。

**English answer:**

I catch specific exceptions only when the pipeline can handle them meaningfully. Record-level validation errors can become rejected records, transient infrastructure errors may be logged and retried, and unknown or unrecoverable errors should be logged with the run ID and stage before being re-raised so the task fails. Logs should include useful context without exposing passwords or sensitive data.

---

## Data modelling and warehousing

### 21. Fact、dimension 和 grain 分别是什么？

**English question:** What are facts, dimensions, and grain?

**中文参考答案：**

Fact table 保存可度量的业务事件，例如交易金额和手续费；dimension table 保存用于描述和筛选事件的实体，例如客户、账户、商户和日期。Grain 定义 fact table 每一行代表什么，必须在选字段前明确。例如 `fct_transaction` 的 grain 可以是“一行代表一笔已接受的银行交易”。如果 grain 不明确，聚合时容易重复计算。

**English answer:**

A fact table stores measurable business events, such as transaction amounts and fees. Dimension tables describe the entities used to filter and analyse those events, such as customers, accounts, merchants, and dates. Grain defines exactly what one fact row represents and should be stated before selecting columns. For `fct_transaction`, the grain could be one accepted banking transaction per row. Unclear grain often causes double counting.

### 22. 什么是 star schema？

**English question:** What is a star schema, and why is it useful?

**中文参考答案：**

Star schema 由中心 fact table 连接多个相对扁平的 dimensions。它适合分析，因为业务含义和 join 路径比较清楚，也便于 BI 工具使用。代价是 dimension 可能存在一定冗余，而且它不是事务写入模型的最佳选择。因此 operational schema 可以保持规范化，analytics schema 再使用 star schema。

**English answer:**

A star schema has a central fact table connected to relatively denormalised dimensions. It is useful for analytics because business meaning and join paths are clear and BI tools can use it easily. The trade-off is some dimensional redundancy, and it is not normally the best model for transactional writes. I would keep the operational schema normalised and use a star schema in the analytics layer.

### 23. 什么是 Slowly Changing Dimension？

**English question:** What is a slowly changing dimension?

**中文参考答案：**

Slowly Changing Dimension 用于处理 dimension 属性随时间变化。Type 1 直接覆盖旧值，不保留历史；Type 2 创建新版本，并使用 effective date、end date 和 current flag 保留历史。例如只关心客户最新地址时可以使用 Type 1；如果风险分析需要知道交易发生时客户所在地区，则可能使用 Type 2。

**English answer:**

A slowly changing dimension manages dimensional attributes that change over time. Type 1 overwrites the previous value and does not preserve history. Type 2 creates a new version and typically uses effective dates, end dates, and a current flag. A current customer address may use Type 1, while risk analysis that needs the customer’s region at transaction time may require Type 2.

### 24. OLTP 和 OLAP 有什么区别？

**English question:** What is the difference between OLTP and OLAP?

**中文参考答案：**

OLTP 面向频繁、小规模、低延迟的事务读写，通常使用规范化模型并强调一致性。OLAP 面向大量扫描、聚合和历史分析，通常使用 columnar storage、fact/dimension 和预聚合。银行交易详情 API 更接近 OLTP 查询；月度趋势和客户风险汇总更接近 OLAP。小型项目可以在一个 PostgreSQL instance 中逻辑分层，但大规模生产系统通常分离工作负载。

**English answer:**

OLTP supports frequent, small, low-latency transactional reads and writes, usually with normalised models and strong consistency. OLAP supports large scans, aggregations, and historical analysis, often using columnar storage, dimensional models, and pre-aggregation. A transaction-detail API is closer to OLTP, while monthly trends and customer-risk summaries are analytical workloads. A small project can separate them logically within PostgreSQL, while larger systems often separate the workloads physically.

---

## dbt, Airflow, Docker, and CI/CD

### 25. dbt 是什么？

**English question:** What is dbt, and where does it fit in a data platform?

**中文参考答案：**

dbt 负责数据库或数仓内部的 SQL transformations、tests、documentation 和 lineage。它通常不负责从外部 API 或文件提取数据，也不是完整 scheduler。在这个项目中，Python ingestion 将数据加载到 raw/core 层，dbt 再构建 staging、intermediate、facts、dimensions 和 marts。CI 可以运行 `dbt build`，确保模型和测试一起通过。

**English answer:**

dbt manages SQL transformations, tests, documentation, and lineage inside a database or warehouse. It does not normally extract data from external APIs or files, and it is not a complete scheduler. In this project, Python ingestion loads data into raw or core tables, then dbt builds staging, intermediate, fact, dimension, and mart models. CI can run `dbt build` so models and tests are validated together.

### 26. Airflow 是什么？

**English question:** What is Airflow used for?

**中文参考答案：**

Airflow 是 workflow orchestrator，负责 schedule、task dependency、retry、timeout、backfill 和运行状态。业务转换逻辑不应该全部堆在 DAG 文件里；DAG 应调用可独立测试的 Python command 或 dbt command。Airflow 的 retry 也不能替代 pipeline 幂等性，因为任务重跑仍必须保证不会重复写入。

**English answer:**

Airflow is a workflow orchestrator that manages schedules, task dependencies, retries, timeouts, backfills, and run status. Business transformation logic should not all live inside DAG files; a DAG should invoke independently testable Python or dbt commands. Airflow retries also do not replace pipeline idempotency, because rerunning a task must still avoid duplicate writes.

### 27. Dockerfile 和 Docker Compose 有什么区别？

**English question:** What is the difference between a Dockerfile and Docker Compose?

**中文参考答案：**

Dockerfile 描述如何构建一个 image，例如安装 Python、依赖和复制应用代码。`compose.yaml` 描述运行哪些 services，以及它们的环境变量、端口、网络、volume、health check 和依赖关系。本地可以由 Compose 启动 PostgreSQL、API 和 migration services；云端通常部署构建好的 API image，并连接 managed PostgreSQL。

**English answer:**

A Dockerfile describes how to build an image, such as installing Python, dependencies, and application code. `compose.yaml` describes which services to run and how they use environment variables, ports, networks, volumes, health checks, and dependencies. Locally, Compose can run PostgreSQL, the API, and migration services. In the cloud, I would normally deploy the built API image and connect it to managed PostgreSQL.

### 28. 你的 CI pipeline 会运行什么？

**English question:** What checks would you include in your CI pipeline?

**中文参考答案：**

Pull request 上先运行 Ruff、pytest 和 lock-file consistency check，然后启动临时 PostgreSQL 运行 migration 和 integration tests。加入 dbt 后运行 `dbt build`，最后构建 Docker image 并执行 smoke test。安全阶段可以增加 dependency 和 image scan。CI 使用测试 secrets，不能连接开发或生产数据库。

**English answer:**

For a pull request, I would run Ruff, pytest, and a lock-file consistency check, then start temporary PostgreSQL for migrations and integration tests. After adding dbt, I would run `dbt build`, then build the Docker image and perform a smoke test. Security stages can include dependency and image scanning. CI must use isolated test credentials and must never connect to development or production databases.

---

## Monitoring, cloud, and behavioural questions

### 29. 如何监控 data pipeline？

**English question:** How would you monitor a data pipeline?

**中文参考答案：**

我会监控 run status、duration、input count、accepted count、rejected count、freshness、retry count 和连续失败次数。日志包含 run ID、source 和 stage，便于关联一次运行的事件。关键失败、文件缺失、数据延迟或数量异常应产生 alert。Dashboard 展示趋势，audit table 支持业务对账，两者不能互相替代。

**English answer:**

I would monitor run status, duration, input counts, accepted and rejected counts, freshness, retry counts, and consecutive failures. Logs should include the run ID, source, and stage so events from one execution can be correlated. Critical failures, missing files, stale data, or unusual volumes should trigger alerts. Dashboards show operational trends, while audit tables support reconciliation; they serve different purposes.

### 30. 本地 PostgreSQL container 可以直接作为生产数据库吗？

**English question:** Would you run PostgreSQL in the same way in local development and production?

**中文参考答案：**

本地开发使用 Docker Compose PostgreSQL 可以保证环境一致并方便清理。生产环境通常优先使用 managed PostgreSQL，以获得备份、维护、监控、恢复和高可用能力。应用通过环境变量连接不同数据库，代码不应依赖本地 host 或 volume。即使使用 managed service，migration、权限、连接池和备份恢复测试仍然需要由团队负责。

**English answer:**

Docker Compose PostgreSQL is useful locally because it provides a consistent and disposable development environment. In production, I would normally prefer managed PostgreSQL for backups, maintenance, monitoring, recovery, and availability features. The application should connect through environment-based configuration rather than depending on a local host or volume. Managed services still require the team to manage migrations, permissions, connection pooling, and recovery testing.

### 31. Dashboard 数据量突然减少一半，怎么排查？

**English question:** A dashboard suddenly shows half the normal transaction volume. How would you investigate it?

**中文参考答案：**

我会先确认时间范围、过滤条件和问题是否可复现，然后从数据链路上游向下游排查：源文件是否完整、是否按时到达、ingestion input count 是否正常、rejected count 是否异常、dbt model 是否成功、数据 freshness 是否正常，以及 dashboard query 是否变化。之后与源系统做 row-count 或金额 reconciliation。修复后安全重跑，并增加能够更早发现同类异常的监控。

**English answer:**

I would first confirm the time range, filters, and whether the issue is reproducible. I would then trace the pipeline from upstream to downstream: source-file completeness and arrival time, ingestion input counts, rejection spikes, dbt model status, data freshness, and dashboard-query changes. I would reconcile row counts or amounts against the source system. After a safe rerun or correction, I would add monitoring to detect the same issue earlier.

### 32. 如果你不知道某个工具，怎么回答？

**English question:** What would you do if you were asked about a technology you have not used?

**中文参考答案：**

我会诚实说明没有生产经验，然后连接到自己理解的相邻概念，并说明学习计划。例如：“我还没有在生产环境使用 Airflow，但我理解它负责 workflow orchestration，包括 dependencies、retry 和 scheduling。我目前使用 CLI 运行 pipeline，后续会用 Airflow DAG 编排 Python ingestion 和 dbt。”这样既不夸大经验，也能展示迁移学习能力。

**English answer:**

I would be honest that I have not used it in production, then connect it to related concepts I understand and explain how I am learning it. For example: “I haven’t used Airflow in production yet, but I understand that it provides workflow orchestration, including dependencies, retries, and scheduling. I currently run my pipeline through a CLI and plan to orchestrate the Python ingestion and dbt steps with an Airflow DAG.”

### 33. 讲一次你解决技术问题的经历

**English question:** Tell me about a difficult technical problem you solved.

**中文答题结构：**

- **Situation：** 描述项目、错误和影响。
- **Task：** 明确你负责定位或修复什么。
- **Action：** 说明如何读取错误、缩小范围、设计测试和验证修复。
- **Result：** 描述结果以及加入了什么预防措施。

**English answer template:**

> In one of my ETL projects, the pipeline failed when source rows contained inconsistent date and amount formats. I was responsible for identifying whether the issue was in parsing, validation, or database loading. I reproduced the failure with a small fixture, separated parsing errors from database errors, and added explicit validation and rejected-record reasons. The pipeline then completed without silently losing invalid records, and I added regression tests for the problematic formats.

### 34. 如何处理不清楚的需求？

**English question:** How do you handle unclear data requirements?

**中文参考答案：**

我会把模糊要求转换成可以确认的业务规则，例如“重复交易”的业务键是什么、金额是原始货币还是账户货币、迟到数据是否修改历史报表。然后用小样例和预期结果与 stakeholder 确认，并把决定记录在 data contract 或 ADR 中。实现时对尚未确认的假设保持可配置，并为边界情况添加测试。

**English answer:**

I turn ambiguous requirements into specific questions, such as the business key for a duplicate transaction, whether an amount is in transaction or account currency, and whether late-arriving data should change historical reports. I confirm the rules with small examples and expected outputs, then record the decisions in a data contract or ADR. Where possible, I keep uncertain assumptions configurable and add tests for agreed edge cases.

---

## Final preparation checklist

面试前应能够脱离笔记回答：

- 60 秒英文自我介绍。
- 2–3 分钟项目架构介绍。
- ETL vs ELT、幂等、重试和 rejected records。
- JOIN、GROUP BY、window function、去重和查询优化。
- Transaction、index、`NUMERIC` 和数据库约束。
- Fact、dimension、grain、star schema 和 SCD。
- dbt、Airflow、Docker Compose 和 CI/CD 的职责边界。
- 一个 debugging STAR 故事和一个 teamwork STAR 故事。

每个写进 CV 的工具都应能回答以下五个问题：

```text
What problem does it solve?
Why did I choose it?
How did I use it?
What are its limitations?
What alternatives did I consider?
```
