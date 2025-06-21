-- Generated Test Case: complex_15
-- Complexity: complex
-- Valid: True
-- Non-Idempotent: False
-- Features: full-text search, GIN index

**Example 6: Full-Text Search**
```sql
CREATE TABLE "full_text_example" (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT NOT NULL
);

INSERT INTO "full_text_example" (name, description) VALUES ('John Doe', 'This is a test description');
INSERT INTO "full_text_example" (name, description) VALUES ('Jane Doe', 'This is another test description');

CREATE INDEX "full_text_idx" ON "full_text_example" USING GIN (to_tsvector('english', description));

SELECT * FROM "full_text_example"
WHERE to_tsvector('english', description) @@ to_tsquery('english', 'test');
```