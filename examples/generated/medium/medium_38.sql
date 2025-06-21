-- Generated Test Case: medium_38
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: unique index, check constraint

-- Example 5: Create a materialized view and refresh it
CREATE MATERIALIZED VIEW customer_orders AS
SELECT c.name, o.total
FROM customers c
JOIN orders o ON c.id = o.customer_id;

REFRESH MATERIALIZED VIEW customer_orders;