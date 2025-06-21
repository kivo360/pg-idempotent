-- Generated Test Case: medium_35
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: trigger, trigger function

-- Example 2: Create a function with dollar quotes and use it in a query
CREATE OR REPLACE FUNCTION greet(name text)
RETURNS text AS $$
BEGIN
    RETURN 'Hello, ' || name || '!';
END;
$$ LANGUAGE plpgsql;

SELECT greet('John');