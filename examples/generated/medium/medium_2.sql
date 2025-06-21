-- Generated Test Case: medium_2
-- Complexity: medium
-- Valid: Unknown
-- Non-Idempotent: Unknown

-- Example 1: Custom type with trigger-based validation
CREATE TYPE account_status AS ENUM ('active', 'suspended', 'closed');

CREATE TABLE bank_accounts (
    id SERIAL PRIMARY KEY,
    account_number VARCHAR(20) NOT NULL UNIQUE,
    balance DECIMAL(15,2) NOT NULL DEFAULT 0,
    status account_status NOT NULL,
    last_updated TIMESTAMP WITH TIME ZONE
);

CREATE OR REPLACE FUNCTION validate_balance_status()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.balance < 0 AND NEW.status != 'suspended' THEN
        RAISE EXCEPTION 'Negative balance only allowed for suspended accounts';
    END IF;
    
    IF NEW.status = 'closed' AND NEW.balance != 0 THEN
        RAISE EXCEPTION 'Cannot close account with non-zero balance';
    END IF;
    
    NEW.last_updated = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_validate_balance_status
BEFORE INSERT OR UPDATE ON bank_accounts
FOR EACH ROW EXECUTE FUNCTION validate_balance_status();

-- This will fail if run twice due to the UNIQUE constraint on account_number
INSERT INTO bank_accounts (account_number, balance, status)
VALUES ('ACC123456', 1000.00, 'active');