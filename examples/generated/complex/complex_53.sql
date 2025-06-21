-- Generated Test Case: complex_53
-- Complexity: complex
-- Valid: True
-- Non-Idempotent: False
-- Features: recursive CTEs

**Example 3: Recursive Common Table Expressions (CTEs)**

```sql
CREATE TABLE my_table (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER,
    name VARCHAR(50) NOT NULL
);

INSERT INTO my_table (parent_id, name) VALUES
    (NULL, 'Root'),
    (1, 'Child 1'),
    (1, 'Child 2'),
    (2, 'Grandchild 1'),
    (2, 'Grandchild 2');

WITH RECURSIVE my_cte AS (
    SELECT id, parent_id, name, 0 AS level
    FROM my_table
    WHERE parent_id IS NULL
    UNION ALL
    SELECT t.id, t.parent_id, t.name, level + 1
    FROM my_table t
    JOIN my_cte p ON t.parent_id = p.id
)
SELECT * FROM my_cte;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'my_table') THEN
        RAISE EXCEPTION 'Table my_table does not exist';
    END IF;
END $$;
```

This migration creates a table, inserts some data, and uses a recursive CTE to query the data. If the table does not exist, it raises an exception.