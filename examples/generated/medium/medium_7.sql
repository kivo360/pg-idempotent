-- Generated Test Case: medium_7
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: JSONB

```

**Example 6: Window Function**
```sql
-- Create a table with a window function
CREATE TABLE sales (
  id SERIAL PRIMARY KEY,
  region text NOT NULL,
  amount numeric(10, 2) NOT NULL
);

-- Insert rows to test the window function
INSERT INTO sales (region, amount) VALUES ('North', 100.00);
INSERT INTO sales (region, amount) VALUES ('South', 200.00);
INSERT INTO sales (region, amount) VALUES ('East', 300.00);
INSERT INTO sales (region, amount) VALUES ('West', 400.00);

-- Use a window function to calculate the running total
SELECT region, amount, SUM(amount) OVER (ORDER BY region) AS running_total
FROM sales;