-- Generated Test Case: simple_19
-- Complexity: simple
-- Valid: True
-- Non-Idempotent: False
-- Features: CREATE TABLE, UNIQUE INDEX

-- Example 2: Add a unique index on a column
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    order_date DATE NOT NULL
);
CREATE UNIQUE INDEX idx_orders_customer_id ON orders (customer_id);