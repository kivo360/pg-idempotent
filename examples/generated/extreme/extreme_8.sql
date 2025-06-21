-- Generated Test Case: extreme_8
-- Complexity: extreme
-- Valid: True
-- Non-Idempotent: False
-- Features: materialized views, functions

-- Example 7: Creating a table with a materialized view and a refresh function
CREATE MATERIALIZED VIEW mv_data AS
SELECT * FROM data_table;

CREATE OR REPLACE FUNCTION refresh_mv()
  RETURNS void AS
$$
BEGIN
  REFRESH MATERIALIZED VIEW mv_data;
END;
$$ LANGUAGE plpgsql;