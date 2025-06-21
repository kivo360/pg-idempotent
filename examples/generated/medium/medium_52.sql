-- Generated Test Case: medium_52
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: True
-- Features: RLS, policies

**

**Example 3: Row-Level Security (RLS)**
```sql
-- Create a table with RLS
CREATE TABLE employees (
  id SERIAL PRIMARY KEY,
  name text,
  salary decimal(10, 2),
  department text
);

-- Create a policy that allows managers to see all employees in their department
CREATE POLICY employees_policy ON employees
  FOR SELECT
  USING (department = current_user);

-- Create a role for managers
CREATE ROLE manager;

-- Grant the manager role to a user
GRANT manager TO myuser;

-- Insert some data to test the policy
INSERT INTO employees (name, salary, department)
VALUES ('John Doe', 50000.00, 'Sales'),
       ('Jane Doe', 60000.00, 'Marketing'),
       ('Bob Smith', 70000.00, 'Sales');

-- Test the policy
SET ROLE manager;
SELECT * FROM employees WHERE department = 'Sales';
```

**