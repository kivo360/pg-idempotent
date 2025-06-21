-- Generated Test Case: complex_19
-- Complexity: complex
-- Valid: True
-- Non-Idempotent: False
-- Features: functions with DO blocks, dollar quotes

**

**Example 2: Creating a function with a DO block and using dollar quotes**
```sql
-- Create a function with a DO block
CREATE OR REPLACE FUNCTION my_function()
  RETURNS VOID AS
$$
  DO $$
    DECLARE
      v_variable VARCHAR(50);
    BEGIN
      v_variable := 'Hello, World!';
      RAISE NOTICE '%', v_variable;
    END;
  $$ LANGUAGE plpgsql;
$$ LANGUAGE sql;

-- Call the function
SELECT my_function();
```

**