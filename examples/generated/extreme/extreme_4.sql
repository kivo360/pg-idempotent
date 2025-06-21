-- Generated Test Case: extreme_4
-- Complexity: extreme
-- Valid: True
-- Non-Idempotent: False
-- Features: unique indexes, nested structures

-- Example 3: Creating a table with a deeply nested structure and a unique index
CREATE TABLE nested_table (
  id SERIAL PRIMARY KEY,
  data jsonb NOT NULL
);

CREATE UNIQUE INDEX idx_nested_table_data ON nested_table ((data->>'key1'->>'key2'->>'key3'));