-- Generated Test Case: extreme_35
-- Complexity: extreme
-- Valid: True
-- Non-Idempotent: True
-- Features: circular dependencies, plpgsql

**

**Example 2: Circular Dependencies**
```sql
-- Create two tables with circular dependencies
CREATE TABLE table_a (
  id SERIAL PRIMARY KEY,
  table_b_id INTEGER NOT NULL REFERENCES table_b(id)
);

CREATE TABLE table_b (
  id SERIAL PRIMARY KEY,
  table_a_id INTEGER NOT NULL REFERENCES table_a(id)
);

-- Insert some data to create a circular dependency
INSERT INTO table_a (table_b_id) VALUES (1);
INSERT INTO table_b (table_a_id) VALUES (1);

-- Create a function to resolve the circular dependency
CREATE OR REPLACE FUNCTION resolve_circular_dependency(p_table_a_id INTEGER)
RETURNS INTEGER AS $$
DECLARE
  v_table_b_id INTEGER;
BEGIN
  SELECT table_b_id INTO v_table_b_id FROM table_a WHERE id = p_table_a_id;
  RETURN v_table_b_id;
END;
$$ LANGUAGE plpgsql;

-- Test the function
SELECT resolve_circular_dependency(1);
```

**