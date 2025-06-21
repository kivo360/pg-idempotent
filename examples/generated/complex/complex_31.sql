-- Generated Test Case: complex_31
-- Complexity: complex
-- Valid: True
-- Non-Idempotent: True
-- Features: window functions, recursive CTE

CREATE TABLE sales (
    id SERIAL PRIMARY KEY,
    region VARCHAR(50),
    sales_date DATE,
    amount DECIMAL(10, 2)
);

CREATE FUNCTION get_region_sales(p_region VARCHAR(50)) RETURNS DECIMAL(10, 2) AS $$
DECLARE
    v_sales DECIMAL(10, 2);
BEGIN
    WITH RECURSIVE region_sales AS (
        SELECT region, sales_date, amount, 0 AS level
        FROM sales
        WHERE region = p_region
        UNION ALL
        SELECT s.region, s.sales_date, s.amount, level + 1
        FROM sales s
        JOIN region_sales r ON s.region = r.region AND s.sales_date = r.sales_date + INTERVAL '1 day'
    )
    SELECT SUM(amount) INTO v_sales
    FROM region_sales;
    RETURN v_sales;
END;
$$ LANGUAGE plpgsql;

CREATE WINDOW FUNCTION get_running_total() RETURNS DECIMAL(10, 2) AS $$
DECLARE
    v_total DECIMAL(10, 2);
BEGIN
    SELECT SUM(amount) INTO v_total
    FROM sales
    WHERE sales_date <= CURRENT_DATE;
    RETURN v_total;
END;
$$ LANGUAGE plpgsql;

INSERT INTO sales (region, sales_date, amount) VALUES
    ('North', '2022-01-01', 100.00),
    ('North', '2022-01-02', 200.00),
    ('South', '2022-01-01', 50.00);

-- This migration is non-idempotent because it inserts data into the sales table
```

**Example 5: Creating a table with a DO block and FOREIGN KEY constraint**
```sql