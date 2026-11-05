# PostgreSQL Query Performance Lab

A reproducible PostgreSQL 16 lab for reading execution plans, adding justified indexes, rewriting predicates, and checking that faster-looking queries still return identical results. The default generator creates 100,000 orders; a larger size is one command-line option.

## Architecture and schema

```text
seeded Python generator -> customers.csv + orders.csv -> PostgreSQL
                                                        ├─ baseline queries/plans
                                                        ├─ indexes + rewrites
                                                        └─ optimized plans + equality check
```

`customers` has 10,000 default rows. `orders` has a primary key, customer foreign key, date, constrained status, and positive numeric amount. The default status distribution is intentionally broad enough to discuss selectivity rather than manufacture a perfect index demonstration.

Three query pairs are compared:

1. Monthly completed revenue: a function-wrapped date filter versus a sargable range predicate and partial covering date index.
2. Customer activity: join-then-aggregate versus aggregate-then-join with a partial customer/date covering index.
3. Recent cancelled orders: `lower(status)` versus direct comparison with a selective partial covering index.

The benchmark runs one warm-up plus five measured `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` executions per query and variant. It then executes both versions normally and compares every returned row.

## Setup and reproduction

Prerequisites: Python 3.11+, Docker Compose, and PostgreSQL client tools.

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate                 # Windows: .venv\Scripts\activate
python -m pip install -e '.[dev]'
pytest -q

docker compose up -d
export DATABASE_URL='postgresql://lab_user:replace-with-local-password@localhost:5432/performance_lab'
bash scripts/run_postgres_benchmark.sh
```

The script loads the baseline with no reporting indexes, vacuums/analyzes it, measures [`sql/03_baseline.sql`](sql/03_baseline.sql), applies [`sql/04_indexes.sql`](sql/04_indexes.sql), measures [`sql/05_optimized.sql`](sql/05_optimized.sql), and writes plans, per-run measurements, summary, and equivalence results under `reports/generated/`.

Generate a larger dataset explicitly:

```bash
generate-performance-data --orders 1000000 --customers 10000 --seed 2025
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f sql/01_schema.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f sql/02_load.sql
benchmark-performance-lab --database-url "$DATABASE_URL" --repeats 5
```

Inspect index storage after applying indexes:

```sql
SELECT indexrelname, pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_stat_user_indexes
WHERE relname = 'orders'
ORDER BY indexrelname;
```

## Actual measured results

Local verification on November 5, 2026: **2 tests passed**, and the generator produced 10,000 customers and exactly 100,000 orders.

GitHub Actions then loaded those rows into PostgreSQL 16 and ran one warm-up plus five measured executions per case. Median server execution time:

| Query | Baseline median | Optimized median | Baseline buffers hit | Optimized buffers hit | Representative scan change |
| --- | ---: | ---: | ---: | ---: | --- |
| 1 monthly revenue | 33.027 ms | 16.257 ms | 840 | 139 | Seq Scan → Index Only Scan |
| 2 customer activity | 34.105 ms | 22.952 ms | 968 | 267 | Seq Scan → Index Only Scan in pre-aggregation |
| 3 recent cancellations | 5.733 ms | 0.303 ms | 840 | 8 | Seq Scan → Index Only Scan |

All three equivalence checks were `true`. Shared read blocks were zero in the measured iterations because the warm-up put this small dataset in PostgreSQL/OS cache. Full artifacts are checked in:

- [summary](reports/actual/summary.csv) and [per-run measurements](reports/actual/measurements.csv);
- [equivalence results](reports/actual/equivalence.json);
- six complete [JSON execution plans](reports/actual/plans/).

These numbers describe one ephemeral GitHub Actions runner and this exact data distribution. They do not guarantee that an index or rewrite will improve another workload. Hardware, PostgreSQL settings, table size, cache state, concurrent load, data distribution, and parameter values can change the plan and result.

## How to interpret the tradeoffs

- **Caching:** warm measurements reduce disk noise but do not represent cold starts. Test both when storage behavior matters.
- **Selectivity:** partial indexes help only queries whose predicates imply the index predicate; broad filters may still favor sequential scans.
- **Storage:** three extra indexes consume disk and cache. Measure with `pg_relation_size` instead of assuming their cost.
- **Writes:** inserts, updates, vacuum, and replication must maintain each index, so read improvement has write amplification.
- **Covering indexes:** `INCLUDE` can enable index-only scans, but visibility-map state and heap updates affect whether heap fetches are avoided.
- **Rewrites:** sargability and pre-aggregation can reduce work, but correctness/equivalence must be tested before performance.

## Scope and cleanup

This is a local PostgreSQL project with no AWS implementation, mocked AWS tests, deployment, IAM policy, or cloud costs.

```bash
docker compose down             # retain data
docker compose down --volumes   # destructive: remove lab data
```

Limitations: the generated workload has no concurrent writes; measurements are short and warm-cache; no `pg_stat_statements` history is collected; index build time and size are not included in the checked-in timing table; and 100,000 rows are useful for learning but much smaller than many production fact tables.

## Interview questions and answers

1. **Why use `EXPLAIN ANALYZE` carefully?** It executes the query and adds instrumentation overhead, so avoid unsafe statements and interpret timings as measurements, not estimates alone.
2. **Why can wrapping a column in a function hurt?** It may prevent a normal index condition unless an equivalent expression index exists; a direct range predicate is often sargable.
3. **Why might PostgreSQL ignore an index?** Low selectivity, stale statistics, small tables, random I/O cost, or a cheaper sequential scan can make that rational.
4. **What does an index-only scan require?** The index must contain needed columns, and the visibility map must let PostgreSQL confirm tuple visibility without frequent heap access.
5. **How was correctness protected?** Each baseline and rewrite ran against the same snapshot, with ordered result sets compared row for row before reporting timings.
