-- Generated Test Case: medium_22
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: views, complex query

**

**Example 5: Creating a view with a complex query**
```sql
-- Create a view with a complex query
CREATE VIEW customer_orders AS
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
  SUM(o.total) > 1000.00;
```

**