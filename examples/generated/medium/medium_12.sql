-- Generated Test Case: medium_12
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: RLS, policies

**Example 3: Row-Level Security (RLS)**
```sql
CREATE TABLE employees (
  id serial PRIMARY KEY,
  name text NOT NULL,
  department text NOT NULL,
  salary numeric(10, 2) NOT NULL
);

CREATE POLICY employees_policy ON employees
  USING (department = current_user);

CREATE ROLE hr;
CREATE ROLE manager;

GRANT SELECT ON employees TO hr;
GRANT SELECT ON employees TO manager;

SET ROLE hr;
SELECT * FROM employees WHERE department = 'HR';

SET ROLE manager;
SELECT * FROM employees WHERE department = 'Management';
```