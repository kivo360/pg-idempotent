-- Generated Test Case: extreme_22
-- Complexity: extreme
-- Valid: True
-- Non-Idempotent: False
-- Features: window functions, partitioning, triggers

**Example 5: Window Functions with Partitioning**
```sql
CREATE TABLE window_functions_example (
    id SERIAL PRIMARY KEY,
    value INTEGER NOT NULL,
    partition_key INTEGER NOT NULL
);

CREATE OR REPLACE FUNCTION window_functions_example_trigger()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OPNAME = 'INSERT' OR TG_OPNAME = 'UPDATE') THEN
        IF (ROW_NUMBER() OVER (PARTITION BY partition_key ORDER BY value) > 1) THEN
            RAISE EXCEPTION 'Duplicate value in partition';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER window_functions_example_trigger
BEFORE INSERT OR UPDATE ON window_functions_example
FOR EACH ROW EXECUTE PROCEDURE window_functions_example_trigger();
```
This example creates a table with a partition key and a trigger function that uses window functions to check for duplicate values within each partition.