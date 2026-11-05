"""Generate deterministic customer and order CSVs at a configurable scale."""

from __future__ import annotations

import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path


def generate_data(output_dir: Path, order_count: int = 100_000, customer_count: int = 10_000, seed: int = 2025) -> dict[str, int]:
    rng = random.Random(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "customers.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("customer_id", "customer_name", "region"))
        regions = ("Northeast", "Southeast", "Midwest", "West")
        for customer_id in range(1, customer_count + 1):
            writer.writerow((customer_id, f"Customer {customer_id:05d}", regions[customer_id % len(regions)]))

    start = date(2024, 1, 1)
    statuses = ("completed",) * 7 + ("cancelled",) * 2 + ("pending",)
    with (output_dir / "orders.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("order_id", "customer_id", "order_date", "status", "total_amount"))
        for order_id in range(1, order_count + 1):
            cents = rng.randint(1_000, 100_000)
            writer.writerow(
                (
                    order_id,
                    rng.randint(1, customer_count),
                    (start + timedelta(days=rng.randrange(731))).isoformat(),
                    rng.choice(statuses),
                    f"{cents / 100:.2f}",
                )
            )
    return {"customers": customer_count, "orders": order_count}


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic PostgreSQL performance-lab data")
    parser.add_argument("--output-dir", type=Path, default=Path("data"))
    parser.add_argument("--orders", type=int, default=100_000)
    parser.add_argument("--customers", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=2025)
    args = parser.parse_args()
    print(generate_data(args.output_dir, args.orders, args.customers, args.seed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

