-- Generated Test Case: complex_29
-- Complexity: complex
-- Valid: Unknown
-- Non-Idempotent: Unknown

CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    email VARCHAR(100)
);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sales_team') THEN
        CREATE ROLE sales_team;
    END IF;
    GRANT SELECT, INSERT, UPDATE ON customers TO sales_team;
    REVOKE DELETE ON customers FROM sales_team;
END $$;

INSERT INTO customers (name, email) VALUES
    ('Acme Inc.', 'sales@acme.com'),
    ('Widget Corp.', 'sales@widgetcorp.com');

-- This migration is non-idempotent because it inserts data into the customers table
```

**Example 3: Creating a table with a nested dollar quote and CHECK constraint**
```sql