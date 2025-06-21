-- Generated Test Case: extreme_39
-- Complexity: extreme
-- Valid: Unknown
-- Non-Idempotent: Unknown

**

**Example 6: Window Functions with Multiple Frames**
```sql
-- Create a table with a window function
CREATE TABLE window_table (
  id SERIAL PRIMARY KEY,
  value INTEGER NOT NULL
);

-- Insert some data
INSERT INTO window_table (value) VALUES (1), (2), (3), (4), (5);

-- Create a window function with multiple frames
CREATE OR REPLACE FUNCTION window_function(p_id INTEGER)
RETURNS INTEGER AS $$
DECLARE
  v_result INTEGER;
BEGIN
  SELECT SUM(value) OVER (
    PARTITION BY id
    ORDER BY id
    ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING
  ) INTO v_result
  FROM window_table
  WHERE id = p_id;
  RETURN v_result;
END;
$$ LANGUAGE plpgsql;

-- Test the function
SELECT window_function(3);
```

**