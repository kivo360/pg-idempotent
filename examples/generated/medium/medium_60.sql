-- Generated Test Case: medium_60
-- Complexity: medium
-- Valid: Unknown
-- Non-Idempotent: Unknown

**Example 3: Dollar-Quoted Function and Custom Aggregate**

```sql
-- Create a custom aggregate function
CREATE OR REPLACE FUNCTION _final_avg(state numeric[], value numeric)
RETURNS numeric[] AS $$
BEGIN
    IF state[1] IS NULL THEN
        RETURN ARRAY[value, 1];
    ELSE
        RETURN ARRAY[state[1] + value, state[2] + 1];
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Create a custom aggregate
CREATE AGGREGATE avg(numeric) (
    sfunc = _final_avg,
    stype = numeric[],
    initcond = '{0, 0}'
);

-- Create a table to test the custom aggregate
CREATE TABLE scores (
    id SERIAL PRIMARY KEY,
    score numeric NOT NULL
);

-- Insert some sample data
INSERT INTO scores (score)
VALUES (90), (80), (70);

-- Test the custom aggregate
SELECT avg(score) FROM scores;
```