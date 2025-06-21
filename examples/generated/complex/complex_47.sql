-- Generated Test Case: complex_47
-- Complexity: complex
-- Valid: True
-- Non-Idempotent: True
-- Features: functions, nested dollar quotes

-- Example 5: Creating a materialized view with a recursive CTE and refreshing it
```sql
CREATE MATERIALIZED VIEW employee_hierarchy AS
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

REFRESH MATERIALIZED VIEW employee_hierarchy;

-- This migration is non-idempotent because it creates a materialized view and refreshes it
-- Running it twice will fail because the materialized view already exists
```