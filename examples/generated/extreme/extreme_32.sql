-- Generated Test Case: extreme_32
-- Complexity: extreme
-- Valid: True
-- Non-Idempotent: True
-- Features: window functions, ROW_NUMBER, RANK, DENSE_RANK

CREATE TABLE window_table (
  id SERIAL PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  value INTEGER NOT NULL
);

SELECT name, value,
       ROW_NUMBER() OVER (PARTITION BY name ORDER BY value) AS row_num,
       RANK() OVER (PARTITION BY name ORDER BY value) AS rank,
       DENSE_RANK() OVER (PARTITION BY name ORDER BY value) AS dense_rank
FROM window_table;
```

**EXAMPLE 8: Creating a table with a full-text search index**

```sql