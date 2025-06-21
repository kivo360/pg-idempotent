-- Generated Test Case: simple_20
-- Complexity: simple
-- Valid: True
-- Non-Idempotent: False
-- Features: CREATE TABLE, FOREIGN KEY, REFERENCES

-- Example 3: Create a table with a foreign key constraint
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL
);
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    order_date DATE NOT NULL,
    CONSTRAINT fk_orders_customers FOREIGN KEY (customer_id) REFERENCES customers (id)
);