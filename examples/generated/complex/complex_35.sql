-- Generated Test Case: complex_35
-- Complexity: complex
-- Valid: True
-- Non-Idempotent: False
-- Features: DO block, nested dollar quotes

**Example 1: Nested Dollar Quotes and Recursive CTE**

```sql
DO $$
BEGIN
    CREATE TABLE employees (
        id SERIAL PRIMARY KEY,
        name VARCHAR(50),
        manager_id INTEGER
    );

    INSERT INTO employees (name, manager_id) VALUES ('John', NULL);
    INSERT INTO employees (name, manager_id) VALUES ('Jane', 1);
    INSERT INTO employees (name, manager_id) VALUES ('Bob', 1);

    WITH RECURSIVE employee_hierarchy AS (
        SELECT id, name, manager_id, 0 AS level
        FROM employees
        WHERE manager_id IS NULL
        UNION ALL
        SELECT e.id, e.name, e.manager_id, level + 1
        FROM employees e
        JOIN employee_hierarchy m ON e.manager_id = m.id
    )
    SELECT * FROM employee_hierarchy;
END $$;
```