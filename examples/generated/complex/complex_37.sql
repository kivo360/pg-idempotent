-- Generated Test Case: complex_37
-- Complexity: complex
-- Valid: True
-- Non-Idempotent: False
-- Features: grant/revoke, multiple roles

**Example 3: Grant/Revoke with Multiple Roles**

```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER,
    order_date DATE
);

CREATE ROLE sales_team;
CREATE ROLE customer_service;

GRANT SELECT, INSERT, UPDATE, DELETE ON orders TO sales_team;
GRANT SELECT ON orders TO customer_service;

CREATE ROLE sales_manager;
GRANT sales_team TO sales_manager;

REVOKE INSERT, UPDATE, DELETE ON orders FROM sales_team;
GRANT INSERT, UPDATE, DELETE ON orders TO sales_manager;

INSERT INTO orders (customer_id, order_date) VALUES (1, '2022-01-01');
```