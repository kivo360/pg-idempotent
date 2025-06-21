-- Generated Test Case: medium_5
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: custom aggregates

```

**Example 4: Dollar-Quoted String**
```sql
-- Create a function with a dollar-quoted string
CREATE OR REPLACE FUNCTION get_greeting()
  RETURNS text AS
$$
  SELECT 'Hello, ' || $1 || '!';
$$
LANGUAGE sql;

-- Test the function
SELECT get_greeting('World');