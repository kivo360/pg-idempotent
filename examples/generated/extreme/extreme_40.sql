-- Generated Test Case: extreme_40
-- Complexity: extreme
-- Valid: Unknown
-- Non-Idempotent: Unknown

**

**Example 7: Lateral Joins with Correlated Subqueries**
```sql
-- Create two tables with a lateral join
CREATE TABLE lateral_table_a (
  id SERIAL PRIMARY KEY,
  value INTEGER NOT NULL
);

CREATE TABLE lateral_table_b (
  id SERIAL PRIMARY KEY,
  value INTEGER NOT NULL
);

-- Insert some data
INSERT INTO lateral_table_a (value) VALUES (1), (2), (3);
INSERT INTO lateral_table_b (value) VALUES (4), (5), (6);

-- Create a lateral join with a correlated subquery
SELECT a.value, b.value
FROM lateral_table_a a
CROSS JOIN LATERAL (
  SELECT value
  FROM lateral_table_b
  WHERE value > a.value
  ORDER BY value
  LIMIT 1
) b;
```

**