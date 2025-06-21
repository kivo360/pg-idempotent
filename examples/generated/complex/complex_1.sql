-- EXAMPLE 1: Complex RLS with dollar-quoted functions and dynamic security policies
DO $$
DECLARE
    schema_version int := 1;
BEGIN
    -- Create a table with sensitive data
    CREATE TABLE customer_secrets (
        id SERIAL PRIMARY KEY,
        customer_id INT NOT NULL,
        secret_data TEXT,
        access_role TEXT NOT NULL
    );
    
    -- Populate with test data
    INSERT INTO customer_secrets (customer_id, secret_data, access_role)
    VALUES 
        (1, $$Top secret data $$ || gen_random_uuid(), 'admin'),
        (2, $$Confidential info $$ || gen_random_uuid(), 'manager'),
        (3, $$Private details $$ || gen_random_uuid(), 'user');

-- Create roles with different access levels
CREATE ROLE admin_role;

CREATE ROLE manager_role;

CREATE ROLE user_role;

-- Complex RLS policy using dollar-quoted function
CREATE OR REPLACE FUNCTION check_secret_access()
    RETURNS BOOLEAN LANGUAGE plpgsql AS $inner$
    BEGIN
        IF current_setting('role') = 'admin_role' THEN
            RETURN TRUE;
        ELSIF current_setting('role') = 'manager_role' THEN
            RETURN access_role IN ('manager', 'user');
        ELSIF current_setting('role') = 'user_role' THEN
            RETURN access_role = 'user';
        END IF;
        RETURN FALSE;
    END;
    $inner$;

-- Enable RLS and set policy
ALTER TABLE customer_secrets ENABLE ROW LEVEL SECURITY;

CREATE POLICY secret_access_policy ON customer_secrets USING (check_secret_access ());

-- Dynamic grants with dollar-quoted strings
EXECUTE $grant$
        GRANT SELECT ON customer_secrets TO admin_role;

GRANT SELECT ON customer_secrets TO manager_role;

GRANT SELECT ON customer_secrets TO user_role;

$grant$;

-- Log completion
RAISE NOTICE 'Applied migration version % with complex RLS setup',
schema_version;

END;

$$ LANGUAGE plpgsql;