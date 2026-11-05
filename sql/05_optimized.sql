-- Q1: sargable date predicate matches the partial date index.
SELECT date_trunc('month', order_date)::date AS month,
       COUNT(*) AS order_count,
       SUM(total_amount)::numeric(16,2) AS revenue
FROM orders
WHERE status = 'completed'
  AND order_date >= DATE '2025-01-01'
GROUP BY 1 ORDER BY 1;

-- QUERY_BREAK
-- Q2: aggregate the fact table before joining customer attributes.
WITH customer_totals AS (
  SELECT customer_id, COUNT(*) AS order_count, SUM(total_amount)::numeric(16,2) AS revenue
  FROM orders
  WHERE status = 'completed' AND order_date >= DATE '2025-01-01'
  GROUP BY customer_id
)
SELECT c.customer_id, c.customer_name, t.order_count, t.revenue
FROM customer_totals t JOIN customers c USING (customer_id)
ORDER BY c.customer_id;

-- QUERY_BREAK
-- Q3: direct status comparison can use the covering partial index.
SELECT order_id, customer_id, order_date, total_amount
FROM orders
WHERE status = 'cancelled'
  AND order_date >= DATE '2025-12-01'
  AND order_date < DATE '2026-01-01'
ORDER BY total_amount DESC, order_id
LIMIT 20;

