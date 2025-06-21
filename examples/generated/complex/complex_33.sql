-- Generated Test Case: complex_33
-- Complexity: complex
-- Valid: True
-- Non-Idempotent: True
-- Features: triggers, unique constraints

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50),
    email VARCHAR(100),
    CONSTRAINT unique_username UNIQUE (username)
);

CREATE FUNCTION validate_username(p_username VARCHAR(50)) RETURNS BOOLEAN AS $$
BEGIN
    RETURN p_username NOT IN (SELECT username FROM users);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER validate_username_trigger
BEFORE INSERT OR UPDATE ON users
FOR EACH ROW
EXECUTE PROCEDURE validate_username(NEW.username);

INSERT INTO users (username, email) VALUES
    ('johndoe', 'johndoe@example.com'),
    ('janedoe', 'janedoe@example.com');

-- This migration is non-idempotent because it inserts data into the users table
```

**Example 7: Creating a table with a recursive CTE and FULL OUTER JOIN**
```sql