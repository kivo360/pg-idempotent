-- Generated Test Case: medium_55
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: window functions, SUM, PARTITION BY

**

**Example 6: Window Function**
```sql
-- Create a table with a window function
CREATE TABLE sales (
  id SERIAL PRIMARY KEY,
  region text,
  sales decimal(10, 2)
);

-- Insert some data to test the window function
INSERT INTO sales (region, sales)
VALUES ('North', 100.00),
       ('North', 200.00),
       ('South', 300.00),
       ('South', 400.00);

-- Test the window function
SELECT region, sales, SUM(sales) OVER (PARTITION BY region) AS total_sales
FROM sales;
```

**