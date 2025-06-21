-- Generated Test Case: medium_34
-- Complexity: medium
-- Valid: True
-- Non-Idempotent: False
-- Features: function, dollar quotes

-- Example 1: Create a custom type and a table using it
CREATE TYPE address AS (
    street text,
    city text,
    state text,
    zip integer
);

CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name text NOT NULL,
    address address NOT NULL
);