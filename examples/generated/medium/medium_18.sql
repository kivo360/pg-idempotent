-- Generated Test Case: medium_18
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: functions with dollar quotes, function usage

`:

**Example 1: Creating a custom type and a table with a column of that type**
```sql
-- Create a custom type
CREATE TYPE address AS (
  street text,
  city text,
  state text,
  zip text
);

-- Create a table with a column of the custom type
CREATE TABLE customers (
  id SERIAL PRIMARY KEY,
  name text NOT NULL,
  address address NOT NULL
);

-- Insert some sample data
INSERT INTO customers (name, address)
VALUES
  ('John Doe', ('123 Main St', 'Anytown', 'CA', '12345')),
  ('Jane Doe', ('456 Elm St', 'Othertown', 'NY', '67890'));
```

**