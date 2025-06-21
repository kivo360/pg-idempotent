-- Generated Test Case: simple_39
-- Complexity: simple
-- Valid: True
-- Non-Idempotent: False
-- Features: enums, foreign keys

**Example 6: Create Table with Enum**

```sql
CREATE TYPE order_status AS ENUM ('pending', 'shipped', 'delivered');

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    order_date DATE NOT NULL,
    status order_status NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```