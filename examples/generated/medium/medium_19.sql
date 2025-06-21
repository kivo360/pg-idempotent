-- Generated Test Case: medium_19
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: trigger functions, trigger attachment

**

**Example 2: Creating a function with dollar quotes and using it in a query**
```sql
-- Create a function with dollar quotes
CREATE OR REPLACE FUNCTION greet(name text)
RETURNS text AS $$
BEGIN
  RETURN 'Hello, ' || name || '!';
END;
$$ LANGUAGE plpgsql;

-- Use the function in a query
SELECT greet('John Doe') AS greeting;
```

**