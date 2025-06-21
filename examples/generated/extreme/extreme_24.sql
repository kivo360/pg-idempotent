-- Generated Test Case: extreme_24
-- Complexity: extreme
-- Valid: True
-- Non-Idempotent: False
-- Features: advanced aggregate functions, triggers

**Example 7: Advanced Aggregate Functions**
```sql
CREATE TABLE advanced_aggregate_example (
    id SERIAL PRIMARY KEY,
    value INTEGER NOT NULL
);

CREATE OR REPLACE FUNCTION advanced_aggregate_example_trigger()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OPNAME = 'INSERT' OR TG_OPNAME = 'UPDATE') THEN
        IF (NOT array_agg(NEW.value ORDER BY NEW.value) = '{1,2,3}') THEN
            RAISE EXCEPTION 'Invalid data';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER advanced_aggregate_example_trigger
BEFORE INSERT OR UPDATE ON advanced_aggregate_example
FOR EACH ROW EXECUTE PROCEDURE advanced_aggregate_example_trigger();
```
This example creates a table with an INTEGER column and a trigger function that uses advanced aggregate functions to check if the data is valid.