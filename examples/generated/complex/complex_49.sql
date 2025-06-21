-- Generated Test Case: complex_49
-- Complexity: complex
-- Valid: Unknown
-- Non-Idempotent: Unknown

-- Example 7: Creating a table with a check constraint and inserting data
```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER,
    order_date DATE,
    total DECIMAL(10, 2),
    CHECK (total > 0)
);

INSERT INTO orders (customer_id, order_date, total)
VALUES (1, '2022-01-01', 100.00),
       (2, '2022-01-15', 200.00),
       (3, '2022-02-01', 50.00);

-- This migration is non-idempotent because it creates a table and inserts data
-- Running it twice will fail because the table already exists
```