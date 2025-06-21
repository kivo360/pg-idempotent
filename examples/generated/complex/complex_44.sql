-- Generated Test Case: complex_44
-- Complexity: complex
-- Valid: True
-- Non-Idempotent: True
-- Features: functions, DO blocks, triggers

-- Example 2: Creating a view with a nested dollar quote and granting privileges
```sql
CREATE OR REPLACE VIEW employee_view AS
$$
SELECT id, name, salary
FROM employees
WHERE salary > (SELECT AVG(salary) FROM employees)
$$
LANGUAGE SQL;

GRANT SELECT ON employee_view TO public;

-- This migration is non-idempotent because it creates a view and grants privileges
-- Running it twice will fail because the view already exists
```