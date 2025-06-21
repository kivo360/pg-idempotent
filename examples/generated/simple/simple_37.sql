-- Generated Test Case: simple_37
-- Complexity: simple
-- Valid: True
-- Non-Idempotent: False
-- Features: foreign keys

**Example 4: Create Table with Foreign Key**

```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    order_date DATE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```