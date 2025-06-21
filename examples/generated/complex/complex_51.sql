-- Generated Test Case: complex_51
-- Complexity: complex
-- Valid: True
-- Non-Idempotent: True
-- Features: DO blocks, triggers, functions

**Example 1: Nested Dollar Quotes and DO Blocks**

```sql
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'my_table') THEN
        CREATE TABLE my_table (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) NOT NULL
        );

        INSERT INTO my_table (name) VALUES ('John Doe'), ('Jane Doe');

        CREATE OR REPLACE FUNCTION my_function()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.name := UPPER(NEW.name);
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER my_trigger
        BEFORE INSERT OR UPDATE ON my_table
        FOR EACH ROW
        EXECUTE PROCEDURE my_function();
    ELSE
        RAISE EXCEPTION 'Table my_table already exists';
    END IF;
END $$;
```

This migration creates a table, inserts some data, creates a function, and sets up a trigger. If the table already exists, it raises an exception.