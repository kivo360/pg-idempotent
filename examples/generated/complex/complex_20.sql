-- Generated Test Case: complex_20
-- Complexity: complex
-- Valid: True
-- Non-Idempotent: False
-- Features: composite primary keys, GRANT, REVOKE

**

**Example 3: Creating a table with a composite primary key and granting privileges**
```sql
-- Create a table with a composite primary key
CREATE TABLE orders (
  customer_id INTEGER,
  order_id INTEGER,
  order_date DATE,
  PRIMARY KEY (customer_id, order_id)
);

-- Grant privileges to a role
GRANT SELECT, INSERT, UPDATE, DELETE ON orders TO my_role;

-- Revoke privileges from a role
REVOKE INSERT, UPDATE, DELETE ON orders FROM my_role;
```

**