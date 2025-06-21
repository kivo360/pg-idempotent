-- Generated Test Case: medium_50
-- Complexity: medium
-- Valid: Unknown
-- Non-Idempotent: Unknown

`:

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
CREATE OR REPLACE FUNCTION get_full_address(addr address)
  RETURNS text AS $$
BEGIN
  RETURN addr.street || ', ' || addr.city || ', ' || addr.state || ' ' || addr.zip;
END;
$$ LANGUAGE plpgsql;

-- Insert some data to test the function
INSERT INTO customers (name, address)
VALUES ('John Doe', ('123 Main St', 'Anytown', 'CA', 12345));

-- Test the function
SELECT get_full_address(address) FROM customers WHERE name = 'John Doe';
```

**