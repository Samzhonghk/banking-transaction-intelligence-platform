# Python and SQL Data Engineer Interview Practice

面向 New Zealand Junior / Intermediate Data Engineer 的跨行业中英双语练习题。

题目覆盖电商订单、用户事件、IoT、日志和通用 ETL，不要求具备金融领域知识。

- Python 常考题 20 道。
- PostgreSQL / SQL 常考题 20 道。
- 每题提供中文、英文、难度和考察点。
- 暂不提供答案，建议先独立完成，再进行 code review。

## Practice rules

Python 题建议：

- 使用 Python 3.13 和 type hints。
- 为关键函数写简短 docstring。
- 明确非法输入、空输入和重复输入的处理方式。
- 为边界情况编写 pytest。
- 大文件题避免一次加载全部数据。

SQL 题建议：

- 使用 PostgreSQL 语法。
- 先写清结果 grain。
- 明确 `NULL`、重复记录和并列排名的处理。
- 优先保证正确性，再讨论索引和性能。
- 不使用 `SELECT *` 作为最终答案。

---

# Part 1: Python Interview Questions

## Python 1 — Parse an API event

**难度：** Easy

**中文题目：**

实现 `parse_event(record: dict[str, str]) -> dict[str, object]`。将 `event_id` 保持为字符串，将 `user_id` 转成整数，将 `event_time` 转成带时区的 `datetime`。字段缺失或格式错误时产生明确异常。

**English question:**

Implement `parse_event(record: dict[str, str]) -> dict[str, object]`. Keep `event_id` as a string, convert `user_id` to an integer, and convert `event_time` to a timezone-aware `datetime`. Missing or malformed fields should produce a clear exception.

**考察点：** Type conversion, datetime parsing, validation, exceptions.

## Python 2 — Validate an IoT reading

**难度：** Easy

**中文题目：**

实现传感器数据校验。必填字段为 `device_id`、`recorded_at`、`temperature`；temperature 必须在 -50 到 100 之间。函数应返回结构化 validation result，而不是只返回布尔值。

**English question:**

Validate an IoT sensor reading. Required fields are `device_id`, `recorded_at`, and `temperature`, and the temperature must be between -50 and 100. Return a structured validation result rather than only a boolean.

**考察点：** Required fields, range validation, structured errors.

## Python 3 — Separate accepted and rejected rows

**难度：** Easy

**中文题目：**

给定原始 CSV records 和 validation function，将数据分成 accepted 与 rejected。每条 rejected row 必须保留原始数据、row number 和具体错误原因。单条错误不能终止整个批次。

**English question:**

Given raw CSV records and a validation function, separate the rows into accepted and rejected collections. Each rejected row must retain the original data, row number, and a specific error reason. One invalid row must not terminate the batch.

**考察点：** Error isolation, data structures, auditability.

## Python 4 — Deduplicate application events

**难度：** Easy / Medium

**中文题目：**

给定包含重复 `event_id` 的事件列表，保留 `received_at` 最新的一条。相同时间戳时使用稳定规则决定保留哪条，并说明算法时间复杂度。

**English question:**

Given application events containing duplicate `event_id` values, retain the event with the latest `received_at`. Use a deterministic tie-breaker for equal timestamps and explain the time complexity.

**考察点：** Business keys, dictionaries, deterministic results, complexity.

## Python 5 — Aggregate order metrics

**难度：** Easy

**中文题目：**

按 `customer_id` 计算订单数量、总金额、平均金额和最大金额。金额使用 `Decimal`。明确取消订单以及空输入应如何处理。

**English question:**

Calculate order count, total amount, average amount, and maximum amount by `customer_id`. Use `Decimal` for monetary values. Define how cancelled orders and empty input should be handled.

**考察点：** Grouping, aggregation, `Decimal`, business rules.

## Python 6 — Find the top N products

**难度：** Easy / Medium

**中文题目：**

根据销售数量找出销量最高的 N 个产品。讨论完整排序和 heap 在大数据集上的时间、空间差异，以及并列销量如何处理。

**English question:**

Find the top N products by units sold. Discuss the time and space trade-offs between sorting the full data set and using a heap, and define how ties should be handled.

**考察点：** Sorting, heap, complexity, tie handling.

## Python 7 — Stream a large CSV

**难度：** Medium

**中文题目：**

实现 generator，逐行读取大型 CSV 并产生字典记录。不能一次加载整个文件；需要正确处理 header、空行、文件关闭和编码错误。

**English question:**

Implement a generator that reads a large CSV row by row and yields dictionary records. Do not load the entire file into memory. Correctly handle the header, blank rows, file closing, and encoding errors.

**考察点：** Generators, file handling, memory efficiency, context managers.

## Python 8 — Batch an iterator

**难度：** Medium

**中文题目：**

实现 `batched(iterable, batch_size)`，逐批产生 list。必须支持 generator 输入，不能提前消耗全部数据。定义最后不足一批以及 `batch_size <= 0` 的行为。

**English question:**

Implement `batched(iterable, batch_size)` to yield lists in batches. It must support generator input without consuming everything in advance. Define the behaviour for the final partial batch and for `batch_size <= 0`.

**考察点：** Iterators, lazy evaluation, boundary conditions.

## Python 9 — Flatten nested API JSON

**难度：** Medium

**中文题目：**

将嵌套 API JSON 转成适合数据库加载的扁平 rows。数据包含 customer、address 和多个 order items。说明如何处理缺失对象、空 items 和一对多关系。

**English question:**

Flatten nested API JSON into rows suitable for database loading. The data contains a customer, an address, and multiple order items. Explain how you handle missing objects, empty item lists, and one-to-many relationships.

**考察点：** Nested structures, normalisation, defensive access.

## Python 10 — Validate a JSON configuration

**难度：** Medium

**中文题目：**

读取 JSON pipeline config，校验必需 sections、字段类型、日期格式和正数 batch size。将文件读取、JSON 解析和业务校验拆成不同职责。

**English question:**

Load a JSON pipeline configuration and validate required sections, field types, date formats, and a positive batch size. Separate file reading, JSON parsing, and business validation into distinct responsibilities.

**考察点：** Configuration, separation of concerns, validation.

## Python 11 — Implement retry with backoff

**难度：** Medium

**中文题目：**

实现 retry helper，只重试指定的临时异常，支持最大次数和 backoff。validation error 不应重试，最后一次失败必须保留原始异常。

**English question:**

Implement a retry helper that retries only specified transient exceptions and supports a maximum attempt count and backoff. Validation errors must not be retried, and the original exception must be preserved after the final failure.

**考察点：** Exceptions, retry classification, higher-order functions.

## Python 12 — Rolling website event count

**难度：** Medium / Hard

**中文题目：**

网站事件已按时间排序。对每个用户的每条事件，计算之前五分钟内的事件数量。要求方案优于每条记录扫描全部历史事件。

**English question:**

Website events are sorted by time. For each event, calculate the number of events from the same user during the preceding five minutes. Use an approach better than scanning the full history for every row.

**考察点：** Sliding window, `deque`, grouping, complexity.

## Python 13 — Merge sorted log streams

**难度：** Medium

**中文题目：**

两个 log iterators 分别按 timestamp 排序。实现 lazy generator，将它们合并为一个有序 stream，不能将两个输入全部读入内存。

**English question:**

Two log iterators are independently sorted by timestamp. Implement a lazy generator that merges them into one ordered stream without loading both inputs into memory.

**考察点：** Merge algorithm, iterators, exhaustion handling.

## Python 14 — Model a validated event

**难度：** Medium

**中文题目：**

使用 frozen dataclass 表示已经通过校验的 event。说明为什么原始字符串解析不一定应该放在 dataclass 内，以及 immutable object 对 pipeline 有什么价值。

**English question:**

Use a frozen dataclass to represent a validated event. Explain why raw-string parsing may not belong inside the dataclass and how immutable objects can help a pipeline.

**考察点：** Dataclasses, immutability, domain modelling.

## Python 15 — Design validation exceptions

**难度：** Medium

**中文题目：**

设计 custom validation exception，包含 error code、field name 和安全错误信息。解释为什么日志中不应直接输出密码、token 或完整个人数据。

**English question:**

Design a custom validation exception containing an error code, field name, and safe message. Explain why passwords, tokens, or complete personal data should not be written directly to logs.

**考察点：** Custom exceptions, observability, privacy.

## Python 16 — Reconcile pipeline counts

**难度：** Medium

**中文题目：**

实现 reconciliation function，验证 `source_count == accepted_count + rejected_count`，所有计数必须为非负整数。不一致时返回包含差值和错误代码的结构化结果。

**English question:**

Implement a reconciliation function that verifies `source_count == accepted_count + rejected_count`, with all counts being non-negative integers. Return a structured result containing the difference and an error code when reconciliation fails.

**考察点：** Invariants, structured results, defensive validation.

## Python 17 — Design an idempotent loader

**难度：** Hard

**中文题目：**

设计一个通用 `load_records()` 接口和伪代码，使同一批 records 重跑不会重复写入。考虑 business key、source checksum、database unique constraint、upsert、transaction 和 run log。

**English question:**

Design the interface and pseudocode for a generic `load_records()` function so rerunning the same batch does not create duplicates. Consider business keys, source checksums, database unique constraints, upserts, transactions, and run logs.

**考察点：** Idempotency, database boundaries, concurrency.

## Python 18 — Parameterised pytest cases

**难度：** Medium

**中文题目：**

使用 `pytest.mark.parametrize` 测试日期解析，覆盖合法 ISO timestamp、无时区时间、空字符串、非法月份、非字符串和 daylight-saving 边界。测试不能依赖真实 `.env`。

**English question:**

Use `pytest.mark.parametrize` to test date parsing with a valid ISO timestamp, a timestamp without a timezone, an empty string, an invalid month, a non-string input, and a daylight-saving boundary. The test must not depend on the real `.env` file.

**考察点：** pytest, timezones, edge cases, isolation.

## Python 19 — Diagnose excessive memory use

**难度：** Medium

**中文题目：**

ETL 处理 5 GB 文件时内存持续增长，代码使用 `list(csv.DictReader(file))`。解释原因，并提出 streaming、batch loading 和内存观测方案。

**English question:**

An ETL process continuously consumes more memory while reading a 5 GB file using `list(csv.DictReader(file))`. Explain the cause and propose streaming, batch-loading, and memory-observation improvements.

**考察点：** Memory complexity, debugging, pipeline design.

## Python 20 — Review unsafe exception handling

**难度：** Medium

**中文题目：**

审查以下代码并提出改进：

```python
try:
    load_records(records)
except Exception:
    pass
```

讨论错误可见性、rollback、重试分类、日志上下文和 run status。

**English question:**

Review the following code and propose a safer design:

```python
try:
    load_records(records)
except Exception:
    pass
```

Discuss error visibility, rollback, retry classification, logging context, and run status.

**考察点：** Reliability, exception handling, logging, failure propagation.

---

# Part 2: SQL Interview Questions

## Shared PostgreSQL schema

SQL 题统一使用一个通用电商与用户事件模型：

```text
customers
├── customer_id       bigint PK
├── customer_name     text
├── country_code      text
└── created_at        timestamptz

orders
├── order_id          bigint PK
├── source_order_id   text
├── customer_id       bigint FK
├── status            text
├── total_amount      numeric(18, 2)
├── ordered_at        timestamptz
└── loaded_at         timestamptz

products
├── product_id        bigint PK
├── product_name      text
├── category          text
└── unit_price        numeric(18, 2)

order_items
├── order_id          bigint FK
├── product_id        bigint FK
├── quantity          integer
└── unit_price        numeric(18, 2)

events
├── event_id          text
├── customer_id       bigint nullable
├── event_type        text
├── page_name         text
├── event_time        timestamptz
└── received_at       timestamptz

pipeline_runs
├── run_id            bigint PK
├── source_name       text
├── source_count      integer
├── accepted_count    integer
├── rejected_count    integer
├── status            text
├── started_at        timestamptz
└── finished_at       timestamptz

rejected_records
├── rejected_id       bigint PK
├── run_id            bigint FK
├── row_number        integer
├── error_code        text
└── rejected_at       timestamptz
```

除非题目另有说明：

- Revenue 只计算 `orders.status = 'COMPLETED'`。
- PostgreSQL 时间按 UTC 保存。
- 金额使用 `numeric`，不转换为 float。

## SQL 1 — Filter recent orders

**难度：** Easy

**中文题目：**

查询最近 30 天内金额大于 500 的已完成订单，返回 order ID、customer ID、amount 和 ordered time，按金额降序、时间升序排列。

**English question:**

Return completed orders from the last 30 days with an amount greater than 500. Select the order ID, customer ID, amount, and order time, ordered by amount descending and time ascending.

**考察点：** Filtering, intervals, ordering.

## SQL 2 — Customer order summary

**难度：** Easy

**中文题目：**

按 customer 统计已完成订单数量、总金额、平均金额和最大金额，只返回至少有 5 个订单的客户。

**English question:**

For each customer, calculate completed order count, total amount, average amount, and maximum amount. Return only customers with at least five completed orders.

**考察点：** Aggregates, `GROUP BY`, `HAVING`.

## SQL 3 — Customers without completed orders

**难度：** Easy / Medium

**中文题目：**

返回从未有过已完成订单的客户。分别考虑完全没有订单以及只有 cancelled 订单的客户。

**English question:**

Return customers who have never had a completed order. Include customers with no orders and customers whose orders are all cancelled.

**考察点：** Anti-join, `NOT EXISTS`, status filtering.

## SQL 4 — Monthly revenue

**难度：** Easy / Medium

**中文题目：**

按自然月统计已完成订单 revenue、订单数量和 unique customer 数量。没有订单的月份是否需要显示？写明假设。

**English question:**

Calculate completed-order revenue, order count, and unique customer count by calendar month. State whether months with no orders should be returned.

**考察点：** Date truncation, aggregates, distinct counts, assumptions.

## SQL 5 — Top three customers per month

**难度：** Medium

**中文题目：**

找出每个月 revenue 最高的三名客户。金额相同获得相同排名，并解释为什么结果可能超过三行。

**English question:**

Find the top three customers by completed-order revenue in each month. Equal totals should receive the same rank. Explain why more than three rows may be returned.

**考察点：** CTE, aggregation, `DENSE_RANK`.

## SQL 6 — Running customer spend

**难度：** Medium

**中文题目：**

为每个已完成订单计算该客户截至当前订单的累计消费金额。相同 ordered time 时使用 order ID 保证稳定排序。

**English question:**

For every completed order, calculate the customer’s running spend up to that order. Use the order ID as a deterministic tie-breaker when order times are equal.

**考察点：** Window `SUM`, partitioning, deterministic ordering.

## SQL 7 — Previous customer event

**难度：** Medium

**中文题目：**

为每条 event 显示该 customer 的上一条 event time，以及两次事件相隔秒数。匿名事件应如何处理？写明假设。

**English question:**

For every event, show the previous event time for the same customer and the number of seconds between the events. State how anonymous events should be handled.

**考察点：** `LAG`, interval calculation, NULL assumptions.

## SQL 8 — Find duplicate events

**难度：** Easy / Medium

**中文题目：**

找出重复的 `event_id`，返回重复数量、最早 received time 和最晚 received time。

**English question:**

Find duplicate `event_id` values and return the occurrence count, earliest received time, and latest received time.

**考察点：** Grouping, `HAVING`, `MIN`, `MAX`.

## SQL 9 — Retain the latest event version

**难度：** Medium

**中文题目：**

为重复 event ID 分配 row number，使 received time 最新的记录为 1。相同 received time 时需要稳定规则。不执行删除。

**English question:**

Assign row numbers to duplicate event IDs so the latest received time is number one. Use a deterministic rule for equal receive times. Do not delete any data.

**考察点：** `ROW_NUMBER`, deduplication, tie-breaking.

## SQL 10 — High-frequency event detection

**难度：** Hard

**中文题目：**

找出任意五分钟窗口内产生至少 20 条事件的 customers，返回 customer ID、触发时间和窗口事件数量。讨论可能的查询方案与索引。

**English question:**

Find customers who generated at least 20 events within any five-minute window. Return the customer ID, triggering time, and event count in the window. Discuss possible query approaches and indexes.

**考察点：** Time windows, correlation, performance.

## SQL 11 — Category revenue percentage

**难度：** Medium

**中文题目：**

按月和 product category 计算销售金额，以及该 category 占当月总销售金额的百分比。需要从 order_items 计算，不能直接按 order total 重复统计。

**English question:**

For each month and product category, calculate sales amount and its percentage of total monthly sales. Calculate from order items without repeatedly counting the full order total.

**考察点：** Multi-table aggregation, window over aggregates, double counting.

## SQL 12 — Latest completed order per customer

**难度：** Medium

**中文题目：**

返回每个客户最新的已完成订单。相同 ordered time 时选择 order ID 最大的记录。比较 `ROW_NUMBER()` 和 PostgreSQL `DISTINCT ON`。

**English question:**

Return the latest completed order for each customer. For equal order times, select the largest order ID. Compare `ROW_NUMBER()` with PostgreSQL `DISTINCT ON`.

**考察点：** Greatest-N-per-group, PostgreSQL syntax.

## SQL 13 — Daily revenue anomaly

**难度：** Medium / Hard

**中文题目：**

计算每日 revenue，并找出超过此前 30 个有销售日平均值两倍的日期。说明历史不足 30 天时如何处理。

**English question:**

Calculate daily revenue and identify days exceeding twice the average of the previous 30 active sales days. Explain how to handle fewer than 30 prior days.

**考察点：** Multi-stage aggregation, window frames, anomaly definitions.

## SQL 14 — Find orphan order items

**难度：** Easy / Medium

**中文题目：**

假设 foreign key 尚未添加，找出引用不存在 order ID 或 product ID 的 order_items。分别给出检查两类 orphan 的查询。

**English question:**

Assuming foreign keys have not yet been added, find order items referencing missing order IDs or product IDs. Provide separate checks for both orphan types.

**考察点：** Referential integrity, anti-joins, data-quality SQL.

## SQL 15 — Reconcile pipeline counts

**难度：** Medium

**中文题目：**

检查每个 run 是否满足 `source_count = accepted_count + rejected_count`，并验证 rejected_records 实际数量等于记录的 rejected count。返回所有差异。

**English question:**

Check whether each run satisfies `source_count = accepted_count + rejected_count`, and verify that the actual rejected-record count equals the recorded rejected count. Return all differences.

**考察点：** Reconciliation, left joins, missing child rows.

## SQL 16 — Weekly pipeline reliability

**难度：** Medium

**中文题目：**

按周计算 pipeline run 数、失败数、失败率和成功 run 的平均 duration。未结束的 run 不进入 duration 计算，并避免整数除法。

**English question:**

For each week, calculate total pipeline runs, failed runs, failure rate, and average duration of successful runs. Unfinished runs must not contribute to duration, and integer division must be avoided.

**考察点：** Conditional aggregation, intervals, filtered aggregates.

## SQL 17 — Upsert an event

**难度：** Medium

**中文题目：**

假设 event ID 有 unique constraint，编写 PostgreSQL upsert。冲突时仅当新的 received time 更晚才更新 event type、page name 和 received time。

**English question:**

Assume the event ID has a unique constraint. Write a PostgreSQL upsert that updates event type, page name, and received time only when the incoming received time is newer.

**考察点：** `ON CONFLICT`, conditional updates, idempotency.

## SQL 18 — Design an API query index

**难度：** Medium / Hard

**中文题目：**

API 经常按 customer ID、status 和 ordered time range 查询订单，并按时间降序分页。提出 composite index，解释列顺序，并比较 offset 和 keyset pagination。

**English question:**

An API frequently filters orders by customer ID, status, and order-time range, then paginates in descending time order. Propose a composite index, explain the column order, and compare offset with keyset pagination.

**考察点：** Index order, selectivity, pagination.

## SQL 19 — Explain a sequential scan

**难度：** Hard

**中文题目：**

查询返回表中约 60% 的 rows，即使有索引仍使用 sequential scan。解释为什么这可能是合理计划，以及如何使用 `EXPLAIN ANALYZE` 和 statistics 验证。

**English question:**

A query returns about 60% of a table and uses a sequential scan despite an available index. Explain why this may be a reasonable plan and how you would verify it using `EXPLAIN ANALYZE` and statistics.

**考察点：** Planner, selectivity, statistics, evidence-based tuning.

## SQL 20 — Customer engagement summary

**难度：** Hard

**中文题目：**

为每个 customer 生成最近 30 天汇总，包括已完成订单数、revenue、不同 product 数、page-view 数、purchase event 数和最近活动时间。需要避免 orders、items 和 events 多表 join 导致重复统计。

**English question:**

Build a 30-day customer summary containing completed-order count, revenue, distinct products, page-view count, purchase-event count, and latest activity time. Avoid double counting caused by joining orders, items, and events at different grains.

**考察点：** Grain, pre-aggregation, multi-source joins, double counting.

---

# Suggested practice order

第一轮：

```text
Python 1–6
SQL 1–9
```

第二轮：

```text
Python 7–16
SQL 10–17
```

第三轮：

```text
Python 17–20
SQL 18–20
```

每题完成后记录：

```text
Assumptions
Time complexity
Edge cases
Tests
Alternative solution
Production considerations
```
