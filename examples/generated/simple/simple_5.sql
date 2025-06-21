-- Generated Test Case: simple_5
-- Complexity: simple
-- Valid: True
-- Non-Idempotent: False
-- Features: unique constraint

**Example 4: Create Table with Foreign Key**
```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    order_date DATE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```
This migration creates an `orders` table with a foreign key `user_id` referencing the `id` column of the `users` table.