-- Generated Test Case: medium_20
-- Complexity: medium
-- Valid: Unknown
-- Non-Idempotent: Unknown

**

**Example 3: Creating a trigger function and attaching it to a table**
```sql
-- Create a trigger function
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create a table with a timestamp column
CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  customer_id INTEGER NOT NULL,
  order_date TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP
);

-- Attach the trigger function to the table
CREATE TRIGGER update_timestamp_trigger
BEFORE UPDATE ON orders
FOR EACH ROW
EXECUTE PROCEDURE update_timestamp();
```

**