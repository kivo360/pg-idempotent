-- Generated Test Case: medium_13
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: jsonb, operators

**Example 4: JSONB Data Type**
```sql
CREATE TABLE products (
  id serial PRIMARY KEY,
  name text NOT NULL,
  attributes jsonb NOT NULL
);

INSERT INTO products (name, attributes)
VALUES ('Product 1', '{"color": "red", "size": "large"}');

SELECT * FROM products WHERE attributes @> '{"color": "red"}';

UPDATE products SET attributes = attributes || '{"material": "wood"}' WHERE id = 1;

SELECT * FROM products WHERE id = 1;
```