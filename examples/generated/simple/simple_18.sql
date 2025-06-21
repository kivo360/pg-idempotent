-- Generated Test Case: simple_18
-- Complexity: simple
-- Valid: True
-- Non-Idempotent: False
-- Features: CREATE TABLE, PRIMARY KEY

-- Example 1: Create a table with a primary key
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL
);