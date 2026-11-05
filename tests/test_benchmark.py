from performance_lab.benchmark import _buffer_totals, load_queries


def test_query_pairs_and_buffer_extraction():
    from pathlib import Path

    root = Path(__file__).parents[1]
    baseline = load_queries(root / "sql" / "03_baseline.sql")
    optimized = load_queries(root / "sql" / "05_optimized.sql")
    assert len(baseline) == len(optimized) == 3
    assert _buffer_totals({"Shared Hit Blocks": 10, "Shared Read Blocks": 2, "Plans": [{"Shared Hit Blocks": 10}]}) == (10, 2)

