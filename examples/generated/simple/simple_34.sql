-- Generated Test Case: simple_34
-- Complexity: simple
-- Valid: True
-- Non-Idempotent: False
-- Features: primary keys, data types

**Example 1: Create Table with Primary Key**

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL
);
```