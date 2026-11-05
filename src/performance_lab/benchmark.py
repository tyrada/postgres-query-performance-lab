"""Capture repeated PostgreSQL plans, timings, buffers, and result equivalence."""

from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
from pathlib import Path

import psycopg


def load_queries(path: Path) -> list[str]:
    return [part.strip() for part in path.read_text(encoding="utf-8").split("-- QUERY_BREAK") if part.strip()]


def _buffer_totals(node: dict) -> tuple[int, int]:
    # The top plan node reports totals for the statement; summing child nodes
    # would double-count blocks represented at multiple levels of the tree.
    return int(node.get("Shared Hit Blocks", 0)), int(node.get("Shared Read Blocks", 0))


def benchmark(database_url: str, sql_dir: Path, output_dir: Path, repeats: int = 5) -> list[dict[str, object]]:
    baseline = load_queries(sql_dir / "03_baseline.sql")
    optimized = load_queries(sql_dir / "05_optimized.sql")
    if len(baseline) != len(optimized):
        raise ValueError("baseline and optimized query counts differ")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "plans").mkdir(exist_ok=True)
    measurements: list[dict[str, object]] = []
    equivalence: dict[str, bool] = {}

    with psycopg.connect(database_url, autocommit=True) as connection:
        with connection.cursor() as cursor:
            for statement in (
                "DROP INDEX IF EXISTS idx_orders_completed_date",
                "DROP INDEX IF EXISTS idx_orders_completed_customer_date",
                "DROP INDEX IF EXISTS idx_orders_cancelled_date_amount",
                "VACUUM (ANALYZE) orders",
            ):
                cursor.execute(statement)

            for variant, queries in (("baseline", baseline),):
                _measure_variant(cursor, variant, queries, repeats, output_dir, measurements)

            cursor.execute((sql_dir / "04_indexes.sql").read_text(encoding="utf-8"))
            _measure_variant(cursor, "optimized", optimized, repeats, output_dir, measurements)

            for index, (baseline_query, optimized_query) in enumerate(zip(baseline, optimized), start=1):
                cursor.execute(baseline_query)
                baseline_rows = cursor.fetchall()
                cursor.execute(optimized_query)
                optimized_rows = cursor.fetchall()
                equivalent = baseline_rows == optimized_rows
                equivalence[f"query_{index}"] = equivalent
                if not equivalent:
                    raise AssertionError(f"query {index} results differ")

    with (output_dir / "measurements.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=measurements[0].keys())
        writer.writeheader()
        writer.writerows(measurements)

    summary: list[dict[str, object]] = []
    for variant in ("baseline", "optimized"):
        for query_number in range(1, len(baseline) + 1):
            values = [float(row["execution_ms"]) for row in measurements if row["variant"] == variant and row["query"] == query_number]
            summary.append(
                {
                    "variant": variant, "query": query_number, "runs": len(values),
                    "min_ms": round(min(values), 3), "median_ms": round(statistics.median(values), 3),
                    "mean_ms": round(statistics.mean(values), 3), "max_ms": round(max(values), 3),
                }
            )
    with (output_dir / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=summary[0].keys())
        writer.writeheader()
        writer.writerows(summary)
    (output_dir / "equivalence.json").write_text(json.dumps(equivalence, indent=2) + "\n", encoding="utf-8")
    return summary


def _measure_variant(cursor, variant, queries, repeats, output_dir, measurements) -> None:
    for query_number, query in enumerate(queries, start=1):
        cursor.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}")  # warm-up
        representative = None
        for run in range(1, repeats + 1):
            cursor.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}")
            payload = cursor.fetchone()[0][0]
            representative = payload
            hit, read = _buffer_totals(payload["Plan"])
            measurements.append(
                {
                    "variant": variant, "query": query_number, "run": run,
                    "planning_ms": round(float(payload["Planning Time"]), 3),
                    "execution_ms": round(float(payload["Execution Time"]), 3),
                    "shared_hit_blocks": hit, "shared_read_blocks": read,
                }
            )
        (output_dir / "plans" / f"{variant}_query_{query_number}.json").write_text(json.dumps(representative, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark baseline and indexed PostgreSQL reporting queries")
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL"))
    parser.add_argument("--sql-dir", type=Path, default=Path("sql"))
    parser.add_argument("--output-dir", type=Path, default=Path("reports/generated"))
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    if not args.database_url:
        parser.error("--database-url or DATABASE_URL is required")
    print(json.dumps(benchmark(args.database_url, args.sql_dir, args.output_dir, args.repeats), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
