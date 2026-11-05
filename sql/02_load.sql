\copy customers(customer_id, customer_name, region) FROM 'data/customers.csv' CSV HEADER
\copy orders(order_id, customer_id, order_date, status, total_amount) FROM 'data/orders.csv' CSV HEADER
ANALYZE customers;
ANALYZE orders;

