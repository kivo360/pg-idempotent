-- Generated Test Case: simple_24
-- Complexity: simple
-- Valid: True
-- Non-Idempotent: False
-- Features: default value

-- Example 7: Create a table with a default value for a column
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    hire_date DATE NOT NULL DEFAULT CURRENT_DATE
);