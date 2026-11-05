from performance_lab.generator import generate_data


def test_generator_is_deterministic_and_configurable(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    assert generate_data(first, order_count=1_000, customer_count=100, seed=7) == {"customers": 100, "orders": 1_000}
    generate_data(second, order_count=1_000, customer_count=100, seed=7)
    assert (first / "customers.csv").read_bytes() == (second / "customers.csv").read_bytes()
    assert (first / "orders.csv").read_bytes() == (second / "orders.csv").read_bytes()

