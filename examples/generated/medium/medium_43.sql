-- Generated Test Case: medium_43
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: RLS

**

**Example 2: Trigger Function**
```sql
-- Create a table with a trigger function to update a timestamp column
CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  customer_id integer NOT NULL,
  order_date timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create a trigger function to update the updated_at column
CREATE OR REPLACE FUNCTION update_updated_at()
  RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create a trigger to call the trigger function on update
CREATE TRIGGER update_updated_at_trigger
  BEFORE UPDATE ON orders
  FOR EACH ROW
  EXECUTE PROCEDURE update_updated_at();

-- Insert some data
INSERT INTO orders (customer_id) VALUES (1), (2), (3);
```

**