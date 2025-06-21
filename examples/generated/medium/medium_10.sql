-- Generated Test Case: medium_10
-- Complexity: medium
-- Valid: Unknown
-- Non-Idempotent: Unknown

**Example 1: Custom Type and Function**
```sql
CREATE TYPE address AS (
  street text,
  city text,
  state text,
  zip integer
);

CREATE OR REPLACE FUNCTION get_full_address(address)
  RETURNS text AS $$
  SELECT $1.street || ', ' || $1.city || ', ' || $1.state || ' ' || $1.zip;
$$ LANGUAGE sql IMMUTABLE;

CREATE TABLE customers (
  id serial PRIMARY KEY,
  name text NOT NULL,
  addr address NOT NULL
);

INSERT INTO customers (name, addr) VALUES ('John Doe', ('123 Main St', 'Anytown', 'CA', 12345));

SELECT get_full_address(addr) FROM customers WHERE id = 1;
```