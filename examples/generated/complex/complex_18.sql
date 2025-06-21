-- Generated Test Case: complex_18
-- Complexity: complex
-- Valid: True
-- Non-Idempotent: False
-- Features: recursive CTEs, RLS, functions with DO blocks

`:

**Example 1: Creating a table with a recursive CTE and enabling RLS**
```sql
-- Create a table with a recursive CTE
CREATE TABLE employees (
  id SERIAL PRIMARY KEY,
  name VARCHAR(50),
  manager_id INTEGER
);

-- Create a recursive CTE to get all employees under a manager
CREATE OR REPLACE FUNCTION get_employees_under_manager(p_manager_id INTEGER)
  RETURNS TABLE (id INTEGER, name VARCHAR(50), manager_id INTEGER) AS
$$
  WITH RECURSIVE employees_under_manager AS (
    SELECT id, name, manager_id
    FROM employees
    WHERE manager_id = p_manager_id
    UNION ALL
    SELECT e.id, e.name, e.manager_id
    FROM employees e
    JOIN employees_under_manager m ON e.manager_id = m.id
  )
  SELECT * FROM employees_under_manager;
$$ LANGUAGE sql;

-- Enable RLS on the employees table
ALTER TABLE employees ENABLE ROW LEVEL SECURITY;

-- Create a policy to allow managers to see their direct reports
CREATE POLICY employees_select_policy ON employees FOR SELECT
  USING (manager_id = current_user_id());
```

**