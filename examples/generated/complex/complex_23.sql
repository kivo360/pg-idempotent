-- Generated Test Case: complex_23
-- Complexity: complex
-- Valid: Unknown
-- Non-Idempotent: Unknown

**

**Example 6: Creating a function with a recursive CTE and using dollar quotes**
```sql
-- Create a function with a recursive CTE
CREATE OR REPLACE FUNCTION get_product_hierarchy(p_product_id INTEGER)
  RETURNS TABLE (id INTEGER, name VARCHAR(50), parent_id INTEGER) AS
$$
  WITH RECURSIVE product_hierarchy AS (
    SELECT id, name, parent_id
    FROM products
    WHERE id = p_product_id
    UNION ALL
    SELECT p.id, p.name, p.parent_id
    FROM products p
    JOIN product_hierarchy m ON p.parent_id = m.id
  )
  SELECT * FROM product_hierarchy;
$$ LANGUAGE sql;
```

**