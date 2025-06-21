-- Generated Test Case: extreme_20
-- Complexity: extreme
-- Valid: True
-- Non-Idempotent: True
-- Features: dynamic SQL, triggers

**Example 3: Dynamic SQL with Polymorphic Functions**
```sql
CREATE TABLE dynamic_sql_example (
    id SERIAL PRIMARY KEY,
    data TEXT NOT NULL
);

CREATE OR REPLACE FUNCTION dynamic_sql_example_trigger()
RETURNS TRIGGER AS $$
DECLARE
    sql TEXT;
BEGIN
    sql := 'SELECT * FROM ' || TG_TABLE_NAME || ' WHERE data = ''' || NEW.data || '''';
    EXECUTE sql;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER dynamic_sql_example_trigger
BEFORE INSERT OR UPDATE ON dynamic_sql_example
FOR EACH ROW EXECUTE PROCEDURE dynamic_sql_example_trigger();
```
This example creates a table with a trigger function that uses dynamic SQL to execute a query on the same table. The trigger function uses the `EXECUTE` statement to execute the dynamic SQL query.