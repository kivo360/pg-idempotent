-- Generated Test Case: complex_22
-- Complexity: complex
-- Valid: Unknown
-- Non-Idempotent: Unknown

**

**Example 5: Creating a table with a CHECK constraint and enabling RLS**
```sql
-- Create a table with a CHECK constraint
CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  name VARCHAR(50),
  price DECIMAL(10, 2),
  CHECK (price > 0)
);

-- Enable RLS on the products table
ALTER TABLE products ENABLE ROW LEVEL SECURITY;

-- Create a policy to allow users to see products with a price greater than 10
CREATE POLICY products_select_policy ON products FOR SELECT
  USING (price > 10);
```

**