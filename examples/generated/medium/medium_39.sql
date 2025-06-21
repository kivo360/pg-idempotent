-- Generated Test Case: medium_39
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: view, rule

-- Example 6: Create a table with a unique index and a check constraint
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name text NOT NULL,
    price decimal(10, 2) NOT NULL CHECK (price > 0)
);

CREATE UNIQUE INDEX products_name_unique ON products (name);