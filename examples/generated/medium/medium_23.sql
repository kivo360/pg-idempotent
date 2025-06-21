-- Generated Test Case: medium_23
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: materialized views, complex query

**

**Example 6: Creating a materialized view**
```sql
-- Create a materialized view
CREATE MATERIALIZED VIEW customer_orders_mv AS
SELECT
  c.name,
  o.order_date,
  SUM(o.total) AS total_spent
FROM
  customers c
  JOIN orders o ON c.id = o.customer_id
GROUP BY
  c.name, o.order_date
HAVING
  SUM(o.total) > 1000.00
WITH DATA;
```

**