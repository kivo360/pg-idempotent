-- Generated Test Case: complex_52
-- Complexity: complex
-- Valid: True
-- Non-Idempotent: True
-- Features: RLS, policies, roles

**Example 2: Complex Row-Level Security (RLS)**

```sql
CREATE TABLE my_table (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    role VARCHAR(50) NOT NULL
);

CREATE POLICY my_policy ON my_table
FOR SELECT, INSERT, UPDATE, DELETE
TO PUBLIC
USING (role = 'admin' OR name = current_user);

CREATE ROLE admin;
CREATE ROLE user;

GRANT SELECT, INSERT, UPDATE, DELETE ON my_table TO admin;
GRANT SELECT ON my_table TO user;

INSERT INTO my_table (name, role) VALUES ('John Doe', 'admin'), ('Jane Doe', 'user');

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'my_policy') THEN
        RAISE EXCEPTION 'Policy my_policy does not exist';
    END IF;
END $$;
```

This migration creates a table, sets up RLS, creates roles, grants privileges, and inserts some data. If the policy does not exist, it raises an exception.