-- Generated Test Case: extreme_7
-- Complexity: extreme
-- Valid: True
-- Non-Idempotent: False
-- Features: full-text search indexes, tsvector columns

-- Example 6: Creating a table with a full-text search index and a tsvector column
CREATE TABLE articles (
  id SERIAL PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  content TEXT NOT NULL,
  tsvector TSVECTOR NOT NULL
);

CREATE INDEX idx_articles_tsvector ON articles USING GIN (tsvector);