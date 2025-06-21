-- Generated Test Case: extreme_18
-- Complexity: extreme
-- Valid: True
-- Non-Idempotent: False
-- Features: JSONB, triggers, PL/pgSQL

**Example 1: Deeply Nested JSONB Structure**
```sql
CREATE TABLE nested_jsonb_example (
    id SERIAL PRIMARY KEY,
    data JSONB NOT NULL
);

INSERT INTO nested_jsonb_example (data)
VALUES ('{
    "key1": {
        "key2": {
            "key3": {
                "key4": "value4"
            }
        }
    }
}');

CREATE OR REPLACE FUNCTION nested_jsonb_example_trigger()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OPNAME = 'INSERT' OR TG_OPNAME = 'UPDATE') THEN
        IF (jsonb_path_query_array(TG_TABLE_NAME, 'data', '$.key1.key2.key3.key4') IS NULL) THEN
            RAISE EXCEPTION 'Invalid JSONB structure';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER nested_jsonb_example_trigger
BEFORE INSERT OR UPDATE ON nested_jsonb_example
FOR EACH ROW EXECUTE PROCEDURE nested_jsonb_example_trigger();
```
This example creates a table with a JSONB column and a trigger function that checks the structure of the JSONB data on insert or update. The trigger function uses the `jsonb_path_query_array` function to query the JSONB data and raises an exception if the expected structure is not found.