CREATE INDEX idx_orders_completed_date
  ON orders(order_date) INCLUDE (total_amount, customer_id)
  WHERE status = 'completed';

CREATE INDEX idx_orders_completed_customer_date
  ON orders(customer_id, order_date) INCLUDE (total_amount)
  WHERE status = 'completed';

CREATE INDEX idx_orders_cancelled_date_amount
  ON orders(order_date, total_amount DESC, order_id)
  INCLUDE (customer_id)
  WHERE status = 'cancelled';

ANALYZE orders;

