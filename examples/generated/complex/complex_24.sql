-- Generated Test Case: complex_24
-- Complexity: complex
-- Valid: Unknown
-- Non-Idempotent: Unknown

**

**Example 7: Creating a table with a UNIQUE constraint and granting privileges**
```sql
-- Create a table with a UNIQUE constraint
CREATE TABLE customers (
  id SERIAL PRIMARY KEY,
  email VARCHAR(50) UNIQUE
);

-- Grant privileges to a role
GRANT SELECT, INSERT, UPDATE, DELETE ON customers TO my_role;

-- Revoke privileges from a role
REVOKE INSERT, UPDATE, DELETE ON customers FROM my_role;
```

**