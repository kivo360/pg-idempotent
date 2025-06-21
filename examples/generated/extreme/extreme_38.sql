-- Generated Test Case: extreme_38
-- Complexity: extreme
-- Valid: Unknown
-- Non-Idempotent: Unknown

**

**Example 5: Recursive Common Table Expressions (CTEs)**
```sql
-- Create a table with a recursive structure
CREATE TABLE recursive_table (
  id SERIAL PRIMARY KEY,
  parent_id INTEGER REFERENCES recursive_table(id)
);

-- Insert some data with a recursive structure
INSERT INTO recursive_table (parent_id) VALUES (NULL), (1), (1), (2), (3);

-- Create a recursive CTE to traverse the recursive structure
WITH RECURSIVE recursive_cte AS (
  SELECT id, parent_id, 0 AS level
  FROM recursive_table
  WHERE parent_id IS NULL
  UNION ALL
  SELECT t.id, t.parent_id, level + 1
  FROM recursive_table t
  JOIN recursive_cte p ON t.parent_id = p.id
)
SELECT * FROM recursive_cte;
```

**