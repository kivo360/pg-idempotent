-- Generated Test Case: simple_30
-- Complexity: simple
-- Valid: Unknown
-- Non-Idempotent: Unknown

-- Example 5: Create a new table with a foreign key
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    order_date DATE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);