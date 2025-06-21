-- Generated Test Case: complex_10
-- Complexity: complex
-- Valid: True
-- Non-Idempotent: True
-- Features: nested dollar quote, DO block, trigger

**Example 1: Nested Dollar Quotes and DO Blocks**
```sql
DO $$
BEGIN
    CREATE TABLE IF NOT EXISTS "nested_example" (
        id SERIAL PRIMARY KEY,
        name VARCHAR(50) NOT NULL
    );

    INSERT INTO "nested_example" (name) VALUES ('John Doe');

    CREATE OR REPLACE FUNCTION "nested_example_trigger"()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.name := 'Jane Doe';
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    CREATE TRIGGER "nested_example_trigger"
    BEFORE INSERT ON "nested_example"
    FOR EACH ROW
    EXECUTE PROCEDURE "nested_example_trigger"();
END $$;
```