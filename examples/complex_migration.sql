-- Complex migration example with various PostgreSQL features

-- Create custom types
CREATE TYPE user_status AS ENUM ('active', 'inactive', 'pending', 'suspended');

CREATE TYPE address_type AS (
    street TEXT,
    city TEXT,
    state TEXT,
    zip_code TEXT
);

-- Create main users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    status user_status DEFAULT 'pending',
    address address_type,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create posts table
CREATE TABLE posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    content TEXT,
    is_public BOOLEAN DEFAULT false,
    published_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_users_email ON users (email);

CREATE INDEX idx_users_status ON users (status)
WHERE
    status != 'active';

CREATE INDEX idx_posts_user_id ON posts (user_id);

CREATE INDEX idx_posts_published ON posts (published_at)
WHERE
    published_at IS NOT NULL;

-- Create update timestamp function
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers
CREATE TRIGGER update_users_timestamp
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_posts_timestamp
    BEFORE UPDATE ON posts
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

ALTER TABLE posts ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY users_select_own ON users FOR
SELECT USING (
        id = current_setting('app.current_user_id')::UUID
    );

CREATE POLICY users_update_own ON users
FOR UPDATE
    USING (
        id = current_setting('app.current_user_id')::UUID
    )
WITH
    CHECK (
        id = current_setting('app.current_user_id')::UUID
    );

CREATE POLICY posts_select_public ON posts FOR
SELECT USING (
        is_public = true
        OR user_id = current_setting('app.current_user_id')::UUID
    );

CREATE POLICY posts_insert_own ON posts FOR INSERT
WITH
    CHECK (
        user_id = current_setting('app.current_user_id')::UUID
    );

CREATE POLICY posts_update_own ON posts
FOR UPDATE
    USING (
        user_id = current_setting('app.current_user_id')::UUID
    )
WITH
    CHECK (
        user_id = current_setting('app.current_user_id')::UUID
    );

-- Create roles and grant permissions
CREATE ROLE app_user;

CREATE ROLE app_admin;

GRANT SELECT ON users TO app_user;

GRANT SELECT, INSERT, UPDATE ON posts TO app_user;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_admin;

-- Create a view
CREATE VIEW public_posts AS
SELECT
    p.id,
    p.title,
    p.content,
    p.published_at,
    u.username as author_username,
    u.email as author_email
FROM posts p
    JOIN users u ON p.user_id = u.id
WHERE
    p.is_public = true
    AND p.published_at IS NOT NULL;

-- Grant view permissions
GRANT SELECT ON public_posts TO app_user;

-- Create a complex function with nested dollar quotes
CREATE FUNCTION create_post(
    p_user_id UUID,
    p_title TEXT,
    p_content TEXT,
    p_is_public BOOLEAN DEFAULT false
) RETURNS UUID AS $func$
DECLARE
    v_post_id UUID;
    v_sql TEXT;
BEGIN
    -- Check if user exists and is active
    IF NOT EXISTS (
        SELECT 1 FROM users 
        WHERE id = p_user_id 
        AND status = 'active'
    ) THEN
        RAISE EXCEPTION 'User % is not active or does not exist', p_user_id;
    END IF;
    
    -- Dynamic SQL example
    v_sql := $sql$
        INSERT INTO posts (user_id, title, content, is_public)
        VALUES ($1, $2, $3, $4)
        RETURNING id
    $sql$;
    
    EXECUTE v_sql INTO v_post_id USING p_user_id, p_title, p_content, p_is_public;
    
    -- Log the action
    RAISE NOTICE 'Created post % for user %', v_post_id, p_user_id;
    
    RETURN v_post_id;
END;
$func$ LANGUAGE plpgsql SECURITY DEFINER;

-- Add a comment
COMMENT ON TABLE users IS 'Main users table with authentication info';

COMMENT ON COLUMN posts.is_public IS 'Whether the post is visible to everyone';