-- Generated Test Case: simple_16
-- Complexity: simple
-- Valid: True
-- Non-Idempotent: False
-- Features: CREATE TABLE, NOT NULL

-- Example 7: Create a table with a NOT NULL constraint
CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT
);