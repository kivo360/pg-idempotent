-- Generated Test Case: simple_13
-- Complexity: simple
-- Valid: True
-- Non-Idempotent: False
-- Features: CREATE TABLE, CHECK CONSTRAINT

-- Example 4: Add a check constraint to a column
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    price DECIMAL(10, 2) NOT NULL
);
ALTER TABLE products ADD CONSTRAINT chk_price CHECK (price > 0);