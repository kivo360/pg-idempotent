-- Generated Test Case: simple_7
-- Complexity: simple
-- Valid: True
-- Non-Idempotent: False
-- Features: default value

**Example 6: Create Table with Enum**
```sql
CREATE TYPE order_status AS ENUM ('pending', 'shipped', 'delivered');

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    order_date DATE NOT NULL,
    status order_status NOT NULL
);
```
This migration creates an `orders` table with an `order_status` enum column.