-- Generated Test Case: complex_43
-- Complexity: complex
-- Valid: True
-- Non-Idempotent: True
-- Features: views, nested dollar quotes

-- Example 1: Creating a table with a recursive CTE and enabling RLS
```sql
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    manager_id INTEGER,
    salary DECIMAL(10, 2)
);

CREATE OR REPLACE FUNCTION get_manager_hierarchy()
RETURNS TABLE (id INTEGER, name VARCHAR(50), manager_id INTEGER, level INTEGER) AS
$$
WITH RECURSIVE manager_hierarchy AS (
    SELECT id, name, manager_id, 0 AS level
    FROM employees
    WHERE manager_id IS NULL
    UNION ALL
    SELECT e.id, e.name, e.manager_id, level + 1
    FROM employees e
    JOIN manager_hierarchy m ON e.manager_id = m.id
)
SELECT * FROM manager_hierarchy;
$$
LANGUAGE SQL;

ALTER TABLE employees ENABLE ROW LEVEL SECURITY;

CREATE POLICY employee_policy ON employees FOR SELECT
TO public
USING (get_manager_hierarchy());

-- This migration is non-idempotent because it creates a table and enables RLS
-- Running it twice will fail because the table already exists
```