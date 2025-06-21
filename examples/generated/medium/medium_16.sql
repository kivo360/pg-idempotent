-- Generated Test Case: medium_16
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: full-text search, GIN indexes

**Example 7: Full-Text Search**
```sql
CREATE TABLE articles (
  id serial PRIMARY KEY,
  title text NOT NULL,
  content text NOT NULL
);

INSERT INTO articles (title, content)
VALUES ('Article 1', 'This is a sample article'),
       ('Article 2', 'Another sample article with different content');

CREATE INDEX articles_content_idx ON articles USING GIN (to_tsvector('english', content));

SELECT * FROM articles WHERE to_tsvector('english', content) @@ to_tsquery('english', 'sample & article');
```