-- Generated Test Case: medium_54
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: full-text search, TSVECTOR, TSQUERY

**

**Example 5: Full-Text Search**
```sql
-- Create a table with a full-text search column
CREATE TABLE articles (
  id SERIAL PRIMARY KEY,
  title text,
  content tsvector
);

-- Insert some data to test the full-text search column
INSERT INTO articles (title, content)
VALUES ('Article A', to_tsvector('This is a sample article.')),
       ('Article B', to_tsvector('This is another sample article.'));

-- Test the full-text search column
SELECT * FROM articles WHERE content @@ to_tsquery('sample & article');
```

**