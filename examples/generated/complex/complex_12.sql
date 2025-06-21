-- Generated Test Case: complex_12
-- Complexity: complex
-- Valid: True
-- Non-Idempotent: False
-- Features: recursive CTEs, window functions

**Example 3: Recursive Common Table Expressions (CTEs)**
```sql
CREATE TABLE "recursive_example" (
    id SERIAL PRIMARY KEY,
    parent_id INTEGER,
    name VARCHAR(50) NOT NULL
);

INSERT INTO "recursive_example" (parent_id, name) VALUES (NULL, 'Root');
INSERT INTO "recursive_example" (parent_id, name) VALUES (1, 'Child 1');
INSERT INTO "recursive_example" (parent_id, name) VALUES (1, 'Child 2');
INSERT INTO "recursive_example" (parent_id, name) VALUES (2, 'Grandchild 1');
INSERT INTO "recursive_example" (parent_id, name) VALUES (2, 'Grandchild 2');

WITH RECURSIVE "recursive_cte" AS (
    SELECT id, parent_id, name, 0 AS level
    FROM "recursive_example"
    WHERE parent_id IS NULL
    UNION ALL
    SELECT e.id, e.parent_id, e.name, level + 1
    FROM "recursive_example" e
    JOIN "recursive_cte" p ON e.parent_id = p.id
)
SELECT * FROM "recursive_cte";
```