-- Generated Test Case: medium_51
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: True
-- Features: triggers, functions, PL/pgSQL

**

**Example 2: Trigger Function**
```sql
-- Create a table with a trigger function
CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  customer_id integer,
  order_date date,
  total decimal(10, 2)
);

-- Create a trigger function that updates the customer's total orders
CREATE OR REPLACE FUNCTION update_customer_orders()
  RETURNS TRIGGER AS $$
BEGIN
  UPDATE customers
  SET total_orders = total_orders + 1
  WHERE id = NEW.customer_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create a trigger that calls the function
CREATE TRIGGER update_customer_orders_trigger
  AFTER INSERT ON orders
  FOR EACH ROW
  EXECUTE PROCEDURE update_customer_orders();

-- Insert some data to test the trigger
INSERT INTO customers (name, total_orders)
VALUES ('Jane Doe', 0);

INSERT INTO orders (customer_id, order_date, total)
VALUES (1, '2022-01-01', 100.00);

-- Test the trigger
SELECT * FROM customers WHERE name = 'Jane Doe';
```

**