-- Generated Test Case: medium_48
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: custom types, functions

**

**Example 7: Full-Text Search**
```sql
-- Create a table with a column to store text data
CREATE TABLE documents (
  id SERIAL PRIMARY KEY,
  title text NOT NULL,
  content text NOT NULL
);

-- Insert some data
INSERT INTO documents (title, content) VALUES ('Document 1', 'This is the content of document 1'), ('Document 2', 'This is the content of document 2');

-- Create a full-text index on the content column
CREATE INDEX documents_content_idx ON documents USING GIN (to_tsvector('english', content));

-- Use full-text search to find documents containing a specific word
SELECT * FROM documents WHERE to_tsvector('english', content) @@ to_tsquery('english', 'content');
```

**