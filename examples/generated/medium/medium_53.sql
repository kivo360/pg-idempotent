-- Generated Test Case: medium_53
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: JSONB, JSON operators

**

**Example 4: JSONB Data Type**
```sql
-- Create a table with a JSONB column
CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  name text,
  attributes jsonb
);

-- Insert some data to test the JSONB column
INSERT INTO products (name, attributes)
VALUES ('Product A', '{"color": "red", "size": "large"}'),
       ('Product B', '{"color": "blue", "size": "small"}');

-- Test the JSONB column
SELECT * FROM products WHERE attributes @> '{"color": "red"}';
```

**