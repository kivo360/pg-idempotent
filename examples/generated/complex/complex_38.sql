-- Generated Test Case: complex_38
-- Complexity: complex
-- Valid: True
-- Non-Idempotent: True
-- Features: DO block, dynamic SQL

**Example 4: DO Block with Dynamic SQL**

```sql
DO $$
DECLARE
    table_name VARCHAR(50) := 'my_table';
    column_name VARCHAR(50) := 'my_column';
BEGIN
    EXECUTE format('CREATE TABLE %I (%I INTEGER)', table_name, column_name);
    EXECUTE format('INSERT INTO %I (%I) VALUES (1)', table_name, column_name);
    EXECUTE format('SELECT * FROM %I', table_name);
END $$;
```