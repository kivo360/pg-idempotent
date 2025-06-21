-- Generated Test Case: extreme_31
-- Complexity: extreme
-- Valid: True
-- Non-Idempotent: True
-- Features: lateral join, JSONB

CREATE TABLE lateral_table (
  id SERIAL PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  data JSONB NOT NULL
);

CREATE TABLE lateral_table_data (
  id SERIAL PRIMARY KEY,
  lateral_table_id INTEGER NOT NULL,
  value TEXT NOT NULL
);

SELECT *
FROM lateral_table
CROSS JOIN LATERAL jsonb_array_elements_text(data) AS data(value);
```

**EXAMPLE 7: Creating a table with a window function**

```sql