-- Generated Test Case: complex_45
-- Complexity: complex
-- Valid: True
-- Non-Idempotent: True
-- Features: complex RLS policy, recursive CTE

-- Example 3: Creating a function with a DO block and revoking privileges
```sql
CREATE OR REPLACE FUNCTION update_employee_salary()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.salary < 50000 THEN
        RAISE EXCEPTION 'Salary cannot be less than 50000';
    END IF;
    RETURN NEW;
END;
$$
LANGUAGE plpgsql;

CREATE TRIGGER update_employee_salary_trigger
BEFORE UPDATE ON employees
FOR EACH ROW
EXECUTE PROCEDURE update_employee_salary();

REVOKE UPDATE ON employees FROM public;

-- This migration is non-idempotent because it creates a function and revokes privileges
-- Running it twice will fail because the function already exists
```