-- Generated Test Case: complex_40
-- Complexity: complex
-- Valid: True
-- Non-Idempotent: True
-- Features: recursive CTE, window function

**Example 6: Recursive CTE with Window Function**

```sql
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    manager_id INTEGER,
    salary DECIMAL(10, 2)
);

INSERT INTO employees (name, manager_id, salary) VALUES ('John', NULL, 100000.00);
INSERT INTO employees (name, manager_id, salary) VALUES ('Jane', 1, 80000.00);
INSERT INTO employees (name, manager_id, salary) VALUES ('Bob', 1, 70000.00);

WITH RECURSIVE employee_hierarchy AS (
    SELECT id, name, manager_id, salary, 0 AS level
    FROM employees
    WHERE manager_id IS NULL
    UNION ALL
    SELECT e.id, e.name, e.manager_id, e.salary, level + 1
    FROM employees e
    JOIN employee_hierarchy m ON e.manager_id = m.id
)
SELECT *, ROW_NUMBER() OVER (PARTITION BY manager_id ORDER BY salary DESC) AS row_num
FROM employee_hierarchy;
```