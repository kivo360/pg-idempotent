-- Generated Test Case: medium_44
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: dollar-quoted strings

**

**Example 3: Row-Level Security (RLS)**
```sql
-- Create a table with RLS enabled
CREATE TABLE employees (
  id SERIAL PRIMARY KEY,
  name text NOT NULL,
  department text NOT NULL
);

-- Enable RLS on the table
ALTER TABLE employees ENABLE ROW LEVEL SECURITY;

-- Create a policy to allow only HR to see all employees
CREATE POLICY hr_policy ON employees
  TO ROLE hr
  USING (true)
  WITH CHECK (true);

-- Create a policy to allow employees to see only their own department
CREATE POLICY employee_policy ON employees
  TO ROLE employee
  USING (department = current_user)
  WITH CHECK (department = current_user);

-- Insert some data
INSERT INTO employees (name, department) VALUES ('John Doe', 'HR'), ('Jane Smith', 'Marketing'), ('Bob Johnson', 'Sales');
```

**