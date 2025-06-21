-- Generated Test Case: extreme_30
-- Complexity: extreme
-- Valid: True
-- Non-Idempotent: True
-- Features: recursive CTE, window functions

CREATE TABLE recursive_table (
  id SERIAL PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  parent_id INTEGER
);

WITH RECURSIVE recursive_cte AS (
  SELECT id, name, parent_id, 0 AS level
  FROM recursive_table
  WHERE parent_id IS NULL
  UNION ALL
  SELECT t.id, t.name, t.parent_id, level + 1
  FROM recursive_table t
  JOIN recursive_cte p ON t.parent_id = p.id
)
SELECT * FROM recursive_cte;
```

**EXAMPLE 6: Creating a table with a lateral join**

```sql