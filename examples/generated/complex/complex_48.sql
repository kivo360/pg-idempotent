-- Generated Test Case: complex_48
-- Complexity: complex
-- Valid: True
-- Non-Idempotent: True
-- Features: check constraints, insert statements

-- Example 6: Creating a function with a nested dollar quote and granting execute privileges
```sql
CREATE OR REPLACE FUNCTION get_employee_salary()
RETURNS DECIMAL(10, 2) AS
$$
SELECT AVG(salary)
FROM employees
$$
LANGUAGE SQL;

GRANT EXECUTE ON FUNCTION get_employee_salary() TO public;

-- This migration is non-idempotent because it creates a function and grants execute privileges
-- Running it twice will fail because the function already exists
```