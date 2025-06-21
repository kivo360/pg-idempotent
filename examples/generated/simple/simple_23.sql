-- Generated Test Case: simple_23
-- Complexity: simple
-- Valid: True
-- Non-Idempotent: False
-- Features: index, GIST index

-- Example 6: Add an index on a column with a specific method
CREATE TABLE large_table (
    id SERIAL PRIMARY KEY,
    data TEXT NOT NULL
);
CREATE INDEX idx_large_table_data ON large_table (data) USING GIST;