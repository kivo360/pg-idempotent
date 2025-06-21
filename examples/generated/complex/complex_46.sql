-- Generated Test Case: complex_46
-- Complexity: complex
-- Valid: True
-- Non-Idempotent: True
-- Features: materialized views, recursive CTE

-- Example 4: Creating a table with a complex RLS policy and enabling RLS
```sql
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    email VARCHAR(100),
    country VARCHAR(50)
);

CREATE OR REPLACE FUNCTION get_customer_policy()
RETURNS TABLE (id INTEGER, name VARCHAR(50), email VARCHAR(100), country VARCHAR(50)) AS
$$
SELECT id, name, email, country
FROM customers
WHERE country = 'USA'
OR (country = 'Canada' AND email LIKE '%@example.com')
$$
LANGUAGE SQL;

ALTER TABLE customers ENABLE ROW LEVEL SECURITY;

CREATE POLICY customer_policy ON customers FOR SELECT
TO public
USING (get_customer_policy());

-- This migration is non-idempotent because it creates a table and enables RLS
-- Running it twice will fail because the table already exists
```