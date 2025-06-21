-- Generated Test Case: medium_46
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: window functions

**

**Example 5: Custom Aggregate Function**
```sql
-- Create a custom aggregate function to calculate the average of a set of numbers
CREATE OR REPLACE FUNCTION avg_accumulator(p_state numeric, p_value numeric)
  RETURNS numeric AS $$
BEGIN
  RETURN p_state + p_value;
END;
$$ LANGUAGE plpgsql;

-- Create a custom aggregate function to calculate the average
CREATE AGGREGATE avg(numeric)
  (
    sfunc = avg_accumulator,
    stype = numeric,
    initcond = 0
  );

-- Create a table with a column to store numbers
CREATE TABLE numbers (
  id SERIAL PRIMARY KEY,
  value numeric NOT NULL
);

-- Insert some data
INSERT INTO numbers (value) VALUES (1), (2), (3), (4), (5);

-- Use the custom aggregate function to calculate the average
SELECT avg(value) FROM numbers;
```

**