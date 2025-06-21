-- Generated Test Case: medium_28
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: RLS, policy

-- Example 3: Create a trigger function and attach it to a table
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_timestamp_trigger
BEFORE UPDATE ON customers
FOR EACH ROW
EXECUTE PROCEDURE update_timestamp();