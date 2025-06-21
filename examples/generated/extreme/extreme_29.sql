-- Generated Test Case: extreme_29
-- Complexity: extreme
-- Valid: True
-- Non-Idempotent: True
-- Features: dynamic SQL, plpgsql

CREATE OR REPLACE FUNCTION create_table_with_dynamic_sql()
RETURNS VOID AS $$
DECLARE
  table_name TEXT := 'my_table';
  column_name TEXT := 'my_column';
  data_type TEXT := 'integer';
  sql TEXT;
BEGIN
  sql := format('CREATE TABLE %I (%I %s)', table_name, column_name, data_type);
  EXECUTE sql;
END;
$$ LANGUAGE plpgsql;

SELECT create_table_with_dynamic_sql();
```

**EXAMPLE 5: Creating a table with a recursive common table expression (CTE)**

```sql