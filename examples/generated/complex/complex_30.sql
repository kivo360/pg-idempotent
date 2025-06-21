-- Generated Test Case: complex_30
-- Complexity: complex
-- Valid: Unknown
-- Non-Idempotent: Unknown

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER,
    order_date DATE,
    total DECIMAL(10, 2),
    CONSTRAINT valid_total CHECK (total > 0)
);

CREATE FUNCTION validate_order_total(p_total DECIMAL(10, 2)) RETURNS BOOLEAN AS $$
BEGIN
    RETURN p_total > 0;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER validate_order_total_trigger
BEFORE INSERT OR UPDATE ON orders
FOR EACH ROW
EXECUTE PROCEDURE validate_order_total(NEW.total);

INSERT INTO orders (customer_id, order_date, total) VALUES
    (1, '2022-01-01', 100.00),
    (2, '2022-01-15', 200.00);

-- This migration is non-idempotent because it inserts data into the orders table
```

**Example 4: Creating a table with a recursive CTE and WINDOW function**
```sql