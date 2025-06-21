-- Generated Test Case: extreme_21
-- Complexity: extreme
-- Valid: True
-- Non-Idempotent: False
-- Features: GIN indexes, GiST indexes, triggers

**Example 4: Advanced Indexing with GIN and GiST**
```sql
CREATE TABLE advanced_indexing_example (
    id SERIAL PRIMARY KEY,
    data TSVECTOR NOT NULL
);

CREATE INDEX advanced_indexing_example_gin_idx ON advanced_indexing_example USING GIN (data);

CREATE INDEX advanced_indexing_example_gist_idx ON advanced_indexing_example USING GiST (data);

CREATE OR REPLACE FUNCTION advanced_indexing_example_trigger()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OPNAME = 'INSERT' OR TG_OPNAME = 'UPDATE') THEN
        IF (NOT to_tsvector('english', NEW.data) @@ to_tsquery('english', 'example')) THEN
            RAISE EXCEPTION 'Invalid data';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER advanced_indexing_example_trigger
BEFORE INSERT OR UPDATE ON advanced_indexing_example
FOR EACH ROW EXECUTE PROCEDURE advanced_indexing_example_trigger();
```
This example creates a table with a TSVECTOR column and two indexes, one using GIN and one using GiST. The trigger function checks if the data is valid using the `to_tsvector` and `to_tsquery` functions.