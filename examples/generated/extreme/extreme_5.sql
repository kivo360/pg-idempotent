-- Generated Test Case: extreme_5
-- Complexity: extreme
-- Valid: True
-- Non-Idempotent: True
-- Features: trigger functions, conditional statements

-- Example 4: Creating a table with a trigger function and a conditional statement
CREATE OR REPLACE FUNCTION trigger_function()
  RETURNS TRIGGER AS
$$
BEGIN
  IF (TG_OPNAME = 'INSERT') THEN
    INSERT INTO audit_table (table_name, operation, data) VALUES ('my_table', TG_OPNAME, row_to_json(NEW));
  ELSIF (TG_OPNAME = 'UPDATE') THEN
    INSERT INTO audit_table (table_name, operation, data) VALUES ('my_table', TG_OPNAME, row_to_json(NEW));
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_name
  BEFORE INSERT OR UPDATE ON my_table
  FOR EACH ROW
  EXECUTE PROCEDURE trigger_function();