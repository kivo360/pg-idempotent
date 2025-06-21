-- Generated Test Case: medium_8
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: custom types, functions

```

**Example 7: JSONB Data Type**
```sql
-- Create a table with a JSONB column
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  data jsonb NOT NULL
);

-- Insert a row with JSONB data
INSERT INTO users (data) VALUES ('{"name": "John Doe", " occupation": "Developer"}');

-- Query the JSONB data
SELECT data->>'name' AS name, data->>'occupation' AS occupation
FROM users;