-- Generated Test Case: medium_6
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: window functions

```

**Example 5: Custom Aggregate**
```sql
-- Create a custom aggregate
CREATE AGGREGATE array_concat(anyarray)
  (
    sfunc = array_cat,
    stype = anyarray,
    initcond = '{}'
  );

-- Test the custom aggregate
SELECT array_concat(ARRAY[1, 2, 3], ARRAY[4, 5, 6]);