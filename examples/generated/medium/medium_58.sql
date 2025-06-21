-- Generated Test Case: medium_58
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: True
-- Features: triggers, RLS, policies

**Example 1: Custom Type and Function**

```sql
-- Create a custom type
CREATE TYPE address AS (
    street text,
    city text,
    state text,
    zip integer
);

-- Create a function that uses the custom type
CREATE OR REPLACE FUNCTION get_full_address(p_address address)
RETURNS text AS $$
BEGIN
    RETURN p_address.street || ', ' || p_address.city || ', ' || p_address.state || ' ' || p_address.zip;
END;
$$ LANGUAGE plpgsql;

-- Create a table that uses the custom type
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name text NOT NULL,
    address address NOT NULL
);

-- Insert some sample data
INSERT INTO customers (name, address)
VALUES ('John Doe', ('123 Main St', 'Anytown', 'CA', 12345));
```