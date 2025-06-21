-- Generated Test Case: medium_4
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: dollar-quoted strings

```

**Example 3: Row-Level Security (RLS)**
```sql
-- Create a table with RLS
CREATE TABLE sensitive_data (
  id SERIAL PRIMARY KEY,
  data text NOT NULL
);

-- Create a policy for RLS
CREATE POLICY sensitive_data_policy ON sensitive_data
  FOR SELECT, INSERT, UPDATE, DELETE
  USING (current_user = 'admin');

-- Insert a row to test RLS
INSERT INTO sensitive_data (data) VALUES ('Top secret information');