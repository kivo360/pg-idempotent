-- Generated Test Case: complex_16
-- Complexity: complex
-- Valid: True
-- Non-Idempotent: False
-- Features: JSON data type, JSONB

**Example 7: JSON Data Type**
```sql
CREATE TABLE "json_example" (
    id SERIAL PRIMARY KEY,
    data JSONB NOT NULL
);

INSERT INTO "json_example" (data) VALUES ('{"name": "John Doe", "age": 30}');
INSERT INTO "json_example" (data) VALUES ('{"name": "Jane Doe", "age": 25}');

SELECT * FROM "json_example"
WHERE data @> '{"name": "John Doe"}';
```