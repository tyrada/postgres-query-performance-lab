-- Q1: function-wrapped date filter prevents a simple date range index condition.
SELECT date_trunc('month', order_date)::date AS month,
       COUNT(*) AS order_count,
       SUM(total_amount)::numeric(16,2) AS revenue
FROM orders
WHERE status = 'completed'
  AND date_trunc('month', order_date) >= DATE '2025-01-01'
GROUP BY 1 ORDER BY 1;

-- QUERY_BREAK
-- Q2: join all qualifying rows before aggregation.
SELECT c.customer_id, c.customer_name,
       COUNT(o.order_id) AS order_count,
       SUM(o.total_amount)::numeric(16,2) AS revenue
FROM customers c
JOIN orders o ON o.customer_id = c.customer_id
WHERE o.status = 'completed' AND o.order_date >= DATE '2025-01-01'
GROUP BY c.customer_id, c.customer_name
ORDER BY c.customer_id;

-- QUERY_BREAK
-- Q3: lower(status) prevents use of the partial cancelled-order index.
SELECT order_id, customer_id, order_date, total_amount
FROM orders
WHERE lower(status) = 'cancelled'
  AND order_date >= DATE '2025-12-01'
  AND order_date < DATE '2026-01-01'
ORDER BY total_amount DESC, order_id
LIMIT 20;

