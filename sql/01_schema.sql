DROP TABLE IF EXISTS orders, customers CASCADE;
CREATE TABLE customers (
  customer_id INTEGER PRIMARY KEY,
  customer_name TEXT NOT NULL,
  region TEXT NOT NULL
);
CREATE TABLE orders (
  order_id BIGINT PRIMARY KEY,
  customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
  order_date DATE NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('completed', 'cancelled', 'pending')),
  total_amount NUMERIC(12,2) NOT NULL CHECK (total_amount > 0)
);

