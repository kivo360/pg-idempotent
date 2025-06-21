-- Example 4: Create a table with a recursive CTE and test GRANT/REVOKE
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    parent_id INTEGER
);

INSERT INTO
    categories (name, parent_id)
VALUES ('Electronics', NULL),
    ('Computers', 1),
    ('Laptops', 2),
    ('Desktops', 2);

CREATE OR REPLACE FUNCTION category_hierarchy()
RETURNS TABLE (id INTEGER, name VARCHAR(50), level INTEGER) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE category_hierarchy AS (
        SELECT id, name, 0 AS level
        FROM categories
        WHERE parent_id IS NULL
        UNION ALL
        SELECT c.id, c.name, level + 1
        FROM categories c
        JOIN category_hierarchy p ON c.parent_id = p.id
    )
    SELECT * FROM category_hierarchy;
END;
$$ LANGUAGE plpgsql;

GRANT SELECT ON categories TO public;

REVOKE SELECT ON categories FROM public;