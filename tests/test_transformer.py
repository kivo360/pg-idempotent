"""Tests for the SQL transformer."""
import pytest
from pg_idempotent.transformer.transformer import SQLTransformer


class TestSQLTransformer:
    """Test SQL transformation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.transformer = SQLTransformer()
    
    def test_transform_create_table(self):
        """Test CREATE TABLE transformation."""
        sql = """
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL
);
"""
        result = self.transformer.transform_sql(sql)
        
        assert result.success
        assert result.statement_count == 1
        assert result.transformed_count == 1
        assert "DO $IDEMPOTENT" in result.transformed_sql
        assert "IF NOT EXISTS" in result.transformed_sql
        assert "information_schema.tables" in result.transformed_sql
    
    def test_transform_create_type(self):
        """Test CREATE TYPE transformation."""
        sql = "CREATE TYPE status AS ENUM ('active', 'inactive', 'pending');"
        
        result = self.transformer.transform_sql(sql)
        
        assert result.success
        assert "pg_type" in result.transformed_sql
        assert "typname = 'status'" in result.transformed_sql
    
    def test_already_idempotent(self):
        """Test that already idempotent statements are not transformed."""
        sql = "CREATE OR REPLACE FUNCTION my_func() RETURNS void AS $ BEGIN END; $ LANGUAGE plpgsql;"
        
        result = self.transformer.transform_sql(sql)
        
        assert result.success
        assert result.transformed_count == 0
        assert "CREATE OR REPLACE" in result.transformed_sql
    
    def test_multiple_statements(self):
        """Test transformation of multiple statements."""
        sql = """
CREATE TYPE user_role AS ENUM ('admin', 'user', 'guest');

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    role user_role NOT NULL
);

CREATE INDEX idx_users_role ON users(role);
"""
        result = self.transformer.transform_sql(sql)
        
        assert result.success
        assert result.statement_count == 3
        assert result.transformed_count == 3
        assert result.transformed_sql.count("DO $IDEMPOTENT") == 3
    
    def test_dollar_quoted_strings(self):
        """Test handling of dollar-quoted strings."""
        sql = """
CREATE FUNCTION test_func() RETURNS text AS $
BEGIN
    RETURN 'Hello World';
END;
$ LANGUAGE plpgsql;
"""
        result = self.transformer.transform_sql(sql)
        
        assert result.success
        assert "$" in result.transformed_sql
        assert "$IDEMPOTENT" in result.transformed_sql
    
    def test_create_policy(self):
        """Test CREATE POLICY transformation."""
        sql = """
CREATE POLICY user_policy ON users
    FOR ALL
    USING (user_id = current_user_id());
"""
        result = self.transformer.transform_sql(sql)
        
        assert result.success
        assert "pg_policies" in result.transformed_sql
        assert "policyname = 'user_policy'" in result.transformed_sql
    
    def test_grant_statement(self):
        """Test GRANT transformation."""
        sql = "GRANT SELECT, INSERT ON TABLE users TO app_user;"
        
        result = self.transformer.transform_sql(sql)
        
        assert result.success
        assert "information_schema.table_privileges" in result.transformed_sql
        assert "GRANT SELECT" in result.transformed_sql
        assert "GRANT INSERT" in result.transformed_sql
    
    def test_alter_table(self):
        """Test ALTER TABLE transformation."""
        sql = "ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"
        
        result = self.transformer.transform_sql(sql)
        
        assert result.success
        assert "EXCEPTION" in result.transformed_sql
        assert "duplicate_column" in result.transformed_sql
    
    def test_non_wrappable_statement(self):
        """Test statements that cannot be wrapped."""
        sql = "VACUUM ANALYZE users;"
        
        result = self.transformer.transform_sql(sql)
        
        assert result.success
        assert result.transformed_count == 0
        assert "WARNING: VACUUM cannot be wrapped" in result.transformed_sql
    
    def test_empty_sql(self):
        """Test empty SQL input."""
        result = self.transformer.transform_sql("")
        
        assert result.success
        assert result.statement_count == 0
        assert result.transformed_count == 0
    
    def test_comment_preservation(self):
        """Test that comments are preserved."""
        sql = """
-- This is a comment
CREATE TABLE test (
    id INT PRIMARY KEY  -- inline comment
);
"""
        result = self.transformer.transform_sql(sql)
        
        assert result.success
        assert "This is a comment" in result.transformed_sql
        assert "inline comment" in result.transformed_sql


if __name__ == "__main__":
    pytest.main([__file__, "-v"])