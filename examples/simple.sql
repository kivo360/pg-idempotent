DO $IDEMPOTENT$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'users') THEN
         CREATE TABLE users (     id SERIAL PRIMARY KEY,     email VARCHAR(255) UNIQUE NOT NULL,     status user_status DEFAULT 'pending',     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP )
    END IF;
END $IDEMPOTENT$;

DO $IDEMPOTENT_001$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND indexname = 'idx_users_email') THEN
         CREATE INDEX idx_users_email ON users(email)
    END IF;
END $IDEMPOTENT_001$;

DO $IDEMPOTENT_002$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND indexname = 'idx_users_status') THEN
        CREATE INDEX idx_users_status ON users(status)
    END IF;
END $IDEMPOTENT_002$;