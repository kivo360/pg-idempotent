-- Generated Test Case: medium_47
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: full-text search

**

**Example 6: Window Function**
```sql
-- Create a table with a column to store sales data
CREATE TABLE sales (
  id SERIAL PRIMARY KEY,
  region text NOT NULL,
  sales numeric NOT NULL
);

-- Insert some data
INSERT INTO sales (region, sales) VALUES ('North', 100), ('South', 200), ('East', 300), ('West', 400);

-- Use a window function to calculate the running total of sales by region
SELECT region, sales, SUM(sales) OVER (PARTITION BY region ORDER BY sales) AS running_total
FROM sales;
```

**