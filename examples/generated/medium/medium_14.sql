-- Generated Test Case: medium_14
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: window functions, ranking functions

**Example 5: Window Function**
```sql
CREATE TABLE sales (
  id serial PRIMARY KEY,
  region text NOT NULL,
  amount numeric(10, 2) NOT NULL
);

INSERT INTO sales (region, amount)
VALUES ('North', 100.00),
       ('South', 200.00),
       ('East', 300.00),
       ('West', 400.00);

SELECT region, amount,
       SUM(amount) OVER (PARTITION BY region) AS total_sales,
       RANK() OVER (PARTITION BY region ORDER BY amount DESC) AS sales_rank
FROM sales;
```