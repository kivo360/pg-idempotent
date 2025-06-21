-- Generated Test Case: medium_32
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: check constraint, function

-- Example 7: Create a table with a check constraint using a function
CREATE OR REPLACE FUNCTION validate_email(email text)
RETURNS boolean AS $$
BEGIN
  RETURN email LIKE '%@%.%';
END;
$$ LANGUAGE plpgsql;

CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email text NOT NULL CHECK (validate_email(email))
);