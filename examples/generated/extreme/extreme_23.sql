-- Generated Test Case: extreme_23
-- Complexity: extreme
-- Valid: True
-- Non-Idempotent: False
-- Features: full-text search, trigrams, triggers

**Example 6: Full-Text Search with Trigrams**
```sql
CREATE TABLE full_text_search_example (
    id SERIAL PRIMARY KEY,
    data TEXT NOT NULL
);

CREATE INDEX full_text_search_example_trgm_idx ON full_text_search_example USING GIST (data gin_trgm_ops);

CREATE OR REPLACE FUNCTION full_text_search_example_trigger()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OPNAME = 'INSERT' OR TG_OPNAME = 'UPDATE') THEN
        IF (NOT similarity(NEW.data, 'example') > 0.5) THEN
            RAISE EXCEPTION 'Invalid data';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER full_text_search_example_trigger
BEFORE INSERT OR UPDATE ON full_text_search_example
FOR EACH ROW EXECUTE PROCEDURE full_text_search_example_trigger();
```
This example creates a table with a TEXT column and an index using trigrams. The trigger function checks if the data is similar to a given string using the `similarity` function.