-- Generated Test Case: medium_56
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: CTE, RECURSIVE, JOIN

**

**Example 7: Common Table Expression (CTE)**
```sql
-- Create a table with a CTE
CREATE TABLE employees (
  id SERIAL PRIMARY KEY,
  name text,
  manager_id integer
);

-- Insert some data to test the CTE
INSERT INTO employees (name, manager_id)
VALUES ('John Doe', NULL),
       ('Jane Doe', 1),
       ('Bob Smith', 1),
       ('Alice Johnson', 2);

-- Test the CTE
WITH RECURSIVE employee_hierarchy AS (
  SELECT id, name, manager_id, 0 AS level
  FROM employees
  WHERE manager_id IS NULL
  UNION ALL
  SELECT e.id, e.name, e.manager_id, level + 1
  FROM employees e
  JOIN employee_hierarchy m ON e.manager_id = m.id
)
SELECT * FROM employee_hierarchy;
```

**