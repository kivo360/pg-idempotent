-- Generated Test Case: complex_8
-- Complexity: complex
-- Valid: True
-- Non-Idempotent: True
-- Features: nested dollar quote, DO block, trigger

-- Example 7: Create a table with a recursive CTE and test DO block
CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    parent_id INTEGER
);

INSERT INTO
    departments (name, parent_id)
VALUES ('Sales', NULL),
    ('Marketing', 1),
    ('HR', 1);

CREATE OR REPLACE FUNCTION department_hierarchy()
RETURNS TABLE (id INTEGER, name VARCHAR(50), level INTEGER) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE department_hierarchy AS (
        SELECT id, name, 0 AS level
        FROM departments
        WHERE parent_id IS NULL
        UNION ALL
        SELECT d.id, d.name, level + 1
        FROM departments d
        JOIN department_hierarchy p ON d.parent_id = p.id
    )
    SELECT * FROM department_hierarchy;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    PERFORM department_hierarchy();
END;
$$ LANGUAGE plpgsql;