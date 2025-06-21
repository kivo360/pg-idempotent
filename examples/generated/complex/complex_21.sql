-- Generated Test Case: complex_21
-- Complexity: complex
-- Valid: Unknown
-- Non-Idempotent: Unknown

**

**Example 4: Creating a materialized view with a complex query**
```sql
-- Create a materialized view
CREATE MATERIALIZED VIEW sales_summary AS
  SELECT
    EXTRACT(YEAR FROM order_date) AS year,
    EXTRACT(MONTH FROM order_date) AS month,
    SUM(total_amount) AS total_sales
  FROM orders
  GROUP BY EXTRACT(YEAR FROM order_date), EXTRACT(MONTH FROM order_date);

-- Refresh the materialized view
REFRESH MATERIALIZED VIEW sales_summary;
```

**