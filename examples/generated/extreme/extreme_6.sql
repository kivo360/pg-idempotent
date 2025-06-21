-- Generated Test Case: extreme_6
-- Complexity: extreme
-- Valid: True
-- Non-Idempotent: False
-- Features: window functions, CTEs

-- Example 5: Creating a table with a window function and a common table expression
CREATE TABLE sales (
  id SERIAL PRIMARY KEY,
  date DATE NOT NULL,
  amount DECIMAL(10, 2) NOT NULL
);

WITH ranked_sales AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY date ORDER BY amount DESC) AS rank
  FROM sales
)
SELECT * FROM ranked_sales WHERE rank = 1;