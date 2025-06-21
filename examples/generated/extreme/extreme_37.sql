-- Generated Test Case: extreme_37
-- Complexity: extreme
-- Valid: True
-- Non-Idempotent: True
-- Features: polymorphic functions, ANYELEMENT, plpgsql

**

**Example 4: Polymorphic Functions**
```sql
-- Create a table with a polymorphic column
CREATE TABLE polymorphic_table (
  id SERIAL PRIMARY KEY,
  data ANYELEMENT NOT NULL
);

-- Insert some data with different data types
INSERT INTO polymorphic_table (data) VALUES (1), ('text'), (TRUE);

-- Create a function to handle different data types
CREATE OR REPLACE FUNCTION handle_polymorphic_data(p_data ANYELEMENT)
RETURNS TEXT AS $$
DECLARE
  v_result TEXT;
BEGIN
  CASE
    WHEN p_data IS INTEGER THEN
      v_result := 'Integer: ' || p_data::TEXT;
    WHEN p_data IS TEXT THEN
      v_result := 'Text: ' || p_data;
    WHEN p_data IS BOOLEAN THEN
      v_result := 'Boolean: ' || p_data::TEXT;
  END CASE;
  RETURN v_result;
END;
$$ LANGUAGE plpgsql;

-- Test the function
SELECT handle_polymorphic_data(data) FROM polymorphic_table;
```

**