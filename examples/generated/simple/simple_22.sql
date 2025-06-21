-- Generated Test Case: simple_22
-- Complexity: simple
-- Valid: True
-- Non-Idempotent: False
-- Features: composite primary key

-- Example 5: Create a table with a composite primary key
CREATE TABLE order_items (
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    PRIMARY KEY (order_id, product_id)
);