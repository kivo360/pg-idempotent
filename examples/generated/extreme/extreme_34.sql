-- Generated Test Case: extreme_34
-- Complexity: extreme
-- Valid: True
-- Non-Idempotent: True
-- Features: deeply nested structures, JSONB, plpgsql

**

**Example 1: Deeply Nested Structures**
```sql
-- Create a table with a deeply nested structure
CREATE TABLE nested_table (
  id SERIAL PRIMARY KEY,
  data JSONB NOT NULL DEFAULT '{}'
);

-- Insert some data with nested structures
INSERT INTO nested_table (data)
VALUES ('{"a": {"b": {"c": {"d": {"e": "value"}}}}}'),
       ('{"f": {"g": {"h": {"i": {"j": "value"}}}}}');

-- Create a function to extract a value from the nested structure
CREATE OR REPLACE FUNCTION extract_value(p_data JSONB, p_path TEXT[])
RETURNS TEXT AS $$
DECLARE
  v_value TEXT;
BEGIN
  v_value := p_data #> p_path;
  RETURN v_value;
END;
$$ LANGUAGE plpgsql;

-- Test the function
SELECT extract_value(data, ARRAY['a', 'b', 'c', 'd', 'e']) FROM nested_table WHERE id = 1;
```

**