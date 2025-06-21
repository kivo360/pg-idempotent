-- Generated Test Case: medium_29
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: materialized views

-- Example 4: Create a table with Row-Level Security (RLS)
CREATE TABLE sensitive_data (
  id SERIAL PRIMARY KEY,
  data text NOT NULL
);

CREATE POLICY sensitive_data_policy ON sensitive_data
FOR SELECT
TO public
USING (current_user = 'admin');