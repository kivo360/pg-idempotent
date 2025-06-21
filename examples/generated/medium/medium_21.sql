-- Generated Test Case: medium_21
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: RLS, policy

**

**Example 4: Implementing basic Row-Level Security (RLS)**
```sql
-- Create a table with RLS
CREATE TABLE employees (
  id SERIAL PRIMARY KEY,
  name text NOT NULL,
  department text NOT NULL,
  salary DECIMAL(10, 2) NOT NULL
);

-- Create a policy for RLS
CREATE POLICY employees_policy ON employees
TO PUBLIC
USING (department = CURRENT_USER);

-- Insert some sample data
INSERT INTO employees (name, department, salary)
VALUES
  ('John Doe', 'Sales', 50000.00),
  ('Jane Doe', 'Marketing', 60000.00),
  ('Bob Smith', 'Sales', 70000.00);
```

**