-- Generated Test Case: medium_45
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: custom aggregates

**

**Example 4: Dollar-Quoted String**
```sql
-- Create a table with a column to store a dollar-quoted string
CREATE TABLE scripts (
  id SERIAL PRIMARY KEY,
  script text NOT NULL
);

-- Insert a dollar-quoted string into the table
INSERT INTO scripts (script) VALUES ($$CREATE TABLE test (id SERIAL PRIMARY KEY, name text NOT NULL)$$);

-- Create a function to execute the script
CREATE OR REPLACE FUNCTION execute_script(p_script text)
  RETURNS void AS $$
BEGIN
  EXECUTE p_script;
END;
$$ LANGUAGE plpgsql;

-- Call the function to execute the script
SELECT execute_script(script) FROM scripts;
```

**