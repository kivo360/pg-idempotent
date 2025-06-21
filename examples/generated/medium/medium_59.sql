-- Generated Test Case: medium_59
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: dollar-quoted functions, custom aggregates, PL/pgSQL

**Example 2: Trigger and Basic RLS**

```sql
-- Create a table with basic RLS
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id integer NOT NULL,
    order_date date NOT NULL,
    total decimal(10, 2) NOT NULL
);

-- Create a policy for row-level security
CREATE POLICY orders_policy ON orders FOR SELECT
USING (customer_id = current_user_id());

-- Create a trigger function to update the total column
CREATE OR REPLACE FUNCTION update_total()
RETURNS TRIGGER AS $$
BEGIN
    NEW.total = NEW.quantity * NEW.price;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create a trigger to call the update_total function
CREATE TRIGGER update_total_trigger
BEFORE INSERT OR UPDATE ON orders
FOR EACH ROW
EXECUTE PROCEDURE update_total();

-- Insert some sample data
INSERT INTO orders (customer_id, order_date, quantity, price)
VALUES (1, '2022-01-01', 2, 10.99);
```