-- Generated Test Case: medium_11
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: triggers, functions

**Example 2: Trigger Function**
```sql
CREATE TABLE orders (
  id serial PRIMARY KEY,
  customer_id integer NOT NULL,
  order_date date NOT NULL,
  total numeric(10, 2) NOT NULL
);

CREATE OR REPLACE FUNCTION update_order_total()
  RETURNS TRIGGER AS $$
  BEGIN
    NEW.total := NEW.quantity * NEW.price;
    RETURN NEW;
  END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_order_total_trigger
  BEFORE INSERT OR UPDATE ON orders
  FOR EACH ROW
  EXECUTE PROCEDURE update_order_total();

INSERT INTO orders (customer_id, order_date, quantity, price)
VALUES (1, '2022-01-01', 2, 10.99);

SELECT * FROM orders WHERE id = 1;
```