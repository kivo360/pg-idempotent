-- Generated Test Case: simple_10
-- Complexity: simple
-- Valid: Unknown
-- Non-Idempotent: Unknown

-- Example 1: Create a table with a primary key
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL
);