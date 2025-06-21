-- Generated Test Case: extreme_28
-- Complexity: extreme
-- Valid: True
-- Non-Idempotent: False
-- Features: JSONB, ALTER TABLE

CREATE TABLE nested_table (
  id SERIAL PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  nested JSONB NOT NULL
);

CREATE TABLE nested_table_nested (
  id SERIAL PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  nested JSONB NOT NULL
);

CREATE TABLE nested_table_nested_nested (
  id SERIAL PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  nested JSONB NOT NULL
);

ALTER TABLE nested_table
ADD COLUMN nested_nested JSONB NOT NULL;

ALTER TABLE nested_table_nested
ADD COLUMN nested_nested_nested JSONB NOT NULL;
```

**EXAMPLE 4: Creating a table with a dynamic SQL query**

```sql