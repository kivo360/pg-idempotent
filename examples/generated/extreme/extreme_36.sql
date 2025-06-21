-- Generated Test Case: extreme_36
-- Complexity: extreme
-- Valid: True
-- Non-Idempotent: True
-- Features: dynamic SQL, plpgsql

**

**Example 3: Dynamic SQL**
```sql
-- Create a table with a dynamic column name
CREATE TABLE dynamic_table (
  id SERIAL PRIMARY KEY,
  dynamic_column TEXT NOT NULL
);

-- Create a function to execute dynamic SQL
CREATE OR REPLACE FUNCTION execute_dynamic_sql(p_column_name TEXT)
RETURNS SETOF dynamic_table AS $$
DECLARE
  v_sql TEXT;
BEGIN
  v_sql := format('SELECT * FROM dynamic_table WHERE %I = ''value''', p_column_name);
  RETURN QUERY EXECUTE v_sql;
END;
$$ LANGUAGE plpgsql;

-- Test the function
SELECT * FROM execute_dynamic_sql('dynamic_column');
```

**