-- Generated Test Case: simple_15
-- Complexity: simple
-- Valid: True
-- Non-Idempotent: False
-- Features: CREATE TABLE, DEFAULT VALUE

-- Example 6: Add a default value to a column
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    hire_date DATE NOT NULL DEFAULT CURRENT_DATE
);