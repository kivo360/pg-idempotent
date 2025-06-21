-- Generated Test Case: medium_15
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: CTEs, joins

**Example 6: Common Table Expression (CTE)**
```sql
CREATE TABLE customers (
  id serial PRIMARY KEY,
  name text NOT NULL,
  email text NOT NULL
);

CREATE TABLE orders (
  id serial PRIMARY KEY,
  customer_id integer NOT NULL,
  order_date date NOT NULL
);

INSERT INTO customers (name, email)
VALUES ('John Doe', 'john@example.com'),
       ('Jane Doe', 'jane@example.com');

INSERT INTO orders (customer_id, order_date)
VALUES (1, '2022-01-01'),
       (1, '2022-01-15'),
       (2, '2022-02-01');

WITH customer_orders AS (
  SELECT c.id, c.name, COUNT(o.id) AS order_count
  FROM customers c
  JOIN orders o ON c.id = o.customer_id
  GROUP BY c.id, c.name
)
SELECT * FROM customer_orders WHERE order_count > 1;
```