-- Generated Test Case: complex_36
-- Complexity: complex
-- Valid: True
-- Non-Idempotent: False
-- Features: row-level security, complex policy

**Example 2: Row-Level Security (RLS) with Complex Policy**

```sql
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    email VARCHAR(100),
    country VARCHAR(50)
);

CREATE ROLE sales;
CREATE ROLE marketing;

CREATE POLICY sales_policy ON customers FOR SELECT, INSERT, UPDATE, DELETE
    USING (current_user = 'sales' AND country = 'USA')
    WITH CHECK (current_user = 'sales' AND country = 'USA');

CREATE POLICY marketing_policy ON customers FOR SELECT
    USING (current_user = 'marketing' AND country = 'Canada')
    WITH CHECK (current_user = 'marketing' AND country = 'Canada');

GRANT SELECT, INSERT, UPDATE, DELETE ON customers TO sales;
GRANT SELECT ON customers TO marketing;

INSERT INTO customers (name, email, country) VALUES ('John Doe', 'john@example.com', 'USA');
INSERT INTO customers (name, email, country) VALUES ('Jane Smith', 'jane@example.com', 'Canada');
```