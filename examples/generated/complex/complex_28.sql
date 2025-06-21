-- Generated Test Case: complex_28
-- Complexity: complex
-- Valid: Unknown
-- Non-Idempotent: Unknown

CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    manager_id INTEGER,
    salary DECIMAL(10, 2)
);

CREATE FUNCTION get_manager_name(p_id INTEGER) RETURNS VARCHAR(50) AS $$
DECLARE
    v_name VARCHAR(50);
BEGIN
    WITH RECURSIVE employee_hierarchy AS (
        SELECT id, name, manager_id, 0 AS level
        FROM employees
        WHERE id = p_id
        UNION ALL
        SELECT e.id, e.name, e.manager_id, level + 1
        FROM employees e
        JOIN employee_hierarchy m ON e.manager_id = m.id
    )
    SELECT name INTO v_name
    FROM employee_hierarchy
    WHERE level = 1;
    RETURN v_name;
END;
$$ LANGUAGE plpgsql;

CREATE POLICY employee_select_policy ON employees FOR SELECT
TO PUBLIC
USING (get_manager_name(id) = current_user);

INSERT INTO employees (name, manager_id, salary) VALUES
    ('John Doe', NULL, 100000.00),
    ('Jane Doe', 1, 80000.00),
    ('Bob Smith', 1, 70000.00);

-- This migration is non-idempotent because it inserts data into the employees table
```

**Example 2: Creating a table with a DO block and GRANT/REVOKE**
```sql