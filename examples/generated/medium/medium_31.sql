-- Generated Test Case: medium_31
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: unique index, expression index

-- Example 6: Create a table with a unique index on an expression
CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  customer_id integer NOT NULL,
  total numeric NOT NULL
);

CREATE UNIQUE INDEX orders_total_index ON orders ((total * 100)::integer);