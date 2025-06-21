-- Generated Test Case: complex_6
-- Complexity: complex
-- Valid: True
-- Non-Idempotent: True
-- Features: complex RLS, DO block, policy

```sql
-- Example 5: Create a table with a nested dollar quote and test DO block
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    price DECIMAL(10, 2)
);

INSERT INTO products (name, price) VALUES
    ('Product A', 10.00),
    ('Product B', 20.00);

CREATE OR REPLACE FUNCTION update_price()
RETURNS TRIGGER AS $$
BEGIN
    NEW.price = NEW.price * 1.1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_price_trigger
BEFORE UPDATE ON products
FOR EACH ROW
EXECUTE PROCEDURE update_price();

DO $$
BEGIN
    UPDATE products SET price = price * 1.1;
END;
$$ LANGUAGE plpgsql;

-- This migration will fail if run twice because the table and trigger already exist
```