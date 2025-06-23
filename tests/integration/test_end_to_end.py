"""Comprehensive end-to-end integration tests for pg-idempotent."""

import tempfile
from pathlib import Path
from textwrap import dedent

import pytest

from pg_idempotent.transformer.transformer import SQLTransformer
from pg_idempotent.parser.parser import PostgreSQLParser


class TestEndToEndTransformation:
    """End-to-end transformation tests."""
    
    def test_simple_schema_transformation(self):
        """Test transformation of a simple database schema."""
        sql = dedent("""
            -- Create users table
            CREATE TABLE users (
                id serial PRIMARY KEY,
                email text UNIQUE NOT NULL,
                created_at timestamp DEFAULT now()
            );
            
            -- Create index
            CREATE INDEX idx_users_email ON users(email);
            
            -- Create posts table
            CREATE TABLE posts (
                id serial PRIMARY KEY,
                user_id integer REFERENCES users(id),
                title text NOT NULL,
                content text
            );
        """)
        
        transformer = SQLTransformer()
        result = transformer.transform_sql(sql)
        
        assert result.success
        assert result.statement_count == 3
        assert result.transformed_count == 3
        assert "DO $$" in result.transformed_sql
        assert "IF NOT EXISTS" in result.transformed_sql
        assert "EXCEPTION WHEN" in result.transformed_sql
    
    def test_complex_function_transformation(self):
        """Test transformation with complex functions and triggers."""
        sql = dedent("""
            -- Already idempotent function
            CREATE OR REPLACE FUNCTION update_modified_time()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.modified_at = now();
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            
            -- Non-idempotent trigger
            CREATE TRIGGER update_users_modified
                BEFORE UPDATE ON users
                FOR EACH ROW
                EXECUTE FUNCTION update_modified_time();
            
            -- Complex function with dollar quotes
            CREATE FUNCTION complex_function(param1 text)
            RETURNS TABLE(id int, data text) AS $func$
            DECLARE
                query text := $query$SELECT id, data FROM table WHERE col = $1$query$;
            BEGIN
                RETURN QUERY EXECUTE query USING param1;
            END;
            $func$ LANGUAGE plpgsql;
        """)
        
        transformer = SQLTransformer()
        result = transformer.transform_sql(sql)
        
        assert result.success
        assert result.statement_count == 3
        # First function is already idempotent
        assert result.transformed_count == 2
        assert "CREATE OR REPLACE FUNCTION update_modified_time" in result.transformed_sql
        assert "DO $$" in result.transformed_sql
    
    def test_mixed_statement_types(self):
        """Test transformation with various statement types."""
        sql = dedent("""
            -- Grant permissions
            GRANT SELECT ON users TO readonly;
            
            -- Alter table
            ALTER TABLE users ADD COLUMN status text DEFAULT 'active';
            
            -- Create type
            CREATE TYPE user_status AS ENUM ('active', 'inactive', 'suspended');
            
            -- Create policy
            CREATE POLICY users_policy ON users
                FOR SELECT
                TO public
                USING (status = 'active');
            
            -- Drop if exists (already idempotent)
            DROP TABLE IF EXISTS old_table;
            
            -- Non-wrappable statement
            VACUUM ANALYZE users;
        """)
        
        transformer = SQLTransformer()
        result = transformer.transform_sql(sql)
        
        assert result.success
        assert result.statement_count == 6
        # VACUUM cannot be wrapped, DROP IF EXISTS is already idempotent
        assert result.transformed_count == 4
        assert "VACUUM ANALYZE users;" in result.transformed_sql  # Should remain unchanged
        assert "DROP TABLE IF EXISTS old_table;" in result.transformed_sql  # Should remain unchanged
    
    def test_error_handling_and_recovery(self):
        """Test handling of parse errors and recovery."""
        sql = dedent("""
            -- Valid statement
            CREATE TABLE valid_table (id int);
            
            -- Invalid SQL
            CREATE TALE invalid_syntax;
            
            -- Another valid statement
            CREATE INDEX idx_valid ON valid_table(id);
            
            -- More invalid SQL
            CRATE FUNCTION bad();
            
            -- Final valid statement
            GRANT SELECT ON valid_table TO public;
        """)
        
        transformer = SQLTransformer()
        result = transformer.transform_sql(sql)
        
        # Should still process valid statements
        assert result.success  # Partial success
        assert len(result.errors) > 0
        assert result.statement_count == 5
        # Only valid statements should be transformed
        assert result.transformed_count < 5
        assert "valid_table" in result.transformed_sql
        assert "idx_valid" in result.transformed_sql
    
    def test_nested_dollar_quotes(self):
        """Test handling of nested dollar quotes."""
        sql = dedent("""
            CREATE FUNCTION nested_quotes_example()
            RETURNS void AS $outer$
            DECLARE
                code1 text := $inner1$SELECT 'Hello'$inner1$;
                code2 text := $inner2$
                    DO $nested$
                    BEGIN
                        RAISE NOTICE 'Nested';
                    END;
                    $nested$;
                $inner2$;
            BEGIN
                EXECUTE code1;
                EXECUTE code2;
            END;
            $outer$ LANGUAGE plpgsql;
        """)
        
        transformer = SQLTransformer()
        result = transformer.transform_sql(sql)
        
        assert result.success
        assert result.statement_count == 1
        assert result.transformed_count == 1
        # Check that dollar quotes are preserved
        assert "$outer$" in result.transformed_sql
        assert "$inner1$" in result.transformed_sql
        assert "$inner2$" in result.transformed_sql
        assert "$nested$" in result.transformed_sql
    
    def test_comment_preservation(self):
        """Test that comments are preserved during transformation."""
        sql = dedent("""
            -- This is a header comment
            /* Multi-line comment
               explaining the schema */
            
            CREATE TABLE test (
                id int PRIMARY KEY,  -- inline comment
                name text  /* another inline comment */
            );
            
            -- Comment before index
            CREATE INDEX idx_test ON test(name);  -- trailing comment
        """)
        
        transformer = SQLTransformer()
        result = transformer.transform_sql(sql)
        
        assert result.success
        # Check that comments are preserved
        assert "This is a header comment" in result.transformed_sql
        assert "Multi-line comment" in result.transformed_sql
        assert "inline comment" in result.transformed_sql
        assert "Comment before index" in result.transformed_sql
    
    def test_transaction_statements(self):
        """Test handling of transaction control statements."""
        sql = dedent("""
            BEGIN;
            
            CREATE TABLE in_transaction (id int);
            
            SAVEPOINT sp1;
            
            CREATE INDEX idx_in_transaction ON in_transaction(id);
            
            COMMIT;
        """)
        
        transformer = SQLTransformer()
        result = transformer.transform_sql(sql)
        
        assert result.success
        # Transaction control statements should not be wrapped
        assert "BEGIN;" in result.transformed_sql
        assert "SAVEPOINT sp1;" in result.transformed_sql
        assert "COMMIT;" in result.transformed_sql
        # But CREATE statements should be wrapped
        assert result.transformed_count == 2  # Two CREATE statements
    
    def test_file_transformation_workflow(self):
        """Test complete file transformation workflow."""
        # Create a temporary SQL file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
            f.write(dedent("""
                -- Database schema v1.0
                
                CREATE TABLE accounts (
                    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                    email text UNIQUE NOT NULL,
                    created_at timestamp DEFAULT now()
                );
                
                CREATE INDEX idx_accounts_email ON accounts(email);
                
                CREATE FUNCTION account_full_name(account_id uuid)
                RETURNS text AS $$
                    SELECT first_name || ' ' || last_name
                    FROM accounts
                    WHERE id = account_id;
                $$ LANGUAGE sql;
                
                GRANT SELECT ON accounts TO app_user;
            """))
            input_path = Path(f.name)
        
        try:
            # Transform the file
            transformer = SQLTransformer()
            output_path = input_path.with_suffix('.idempotent.sql')
            
            result = transformer.transform_file(str(input_path), str(output_path))
            
            assert result.success
            assert result.statement_count == 4
            assert result.transformed_count == 4
            assert output_path.exists()
            
            # Read and verify output
            output_content = output_path.read_text()
            assert "DO $$" in output_content
            assert "IF NOT EXISTS" in output_content
            assert "EXCEPTION WHEN" in output_content
            
            # Verify idempotency by running transformation again
            result2 = transformer.transform_file(str(output_path))
            assert result2.success
            # Should recognize that statements are already idempotent
            assert result2.transformed_count < result.transformed_count
            
        finally:
            # Cleanup
            input_path.unlink(missing_ok=True)
            if output_path.exists():
                output_path.unlink()
    
    def test_validation_workflow(self):
        """Test the validation workflow."""
        sql = dedent("""
            CREATE TABLE test (id int);
            CREATE INDEX idx_test ON test(id);
        """)
        
        transformer = SQLTransformer()
        result = transformer.transform_sql(sql)
        
        assert result.success
        
        # Validate the transformed SQL
        validation = transformer.validate_transformed_sql(result.transformed_sql)
        
        assert validation['valid']
        assert len(validation['issues']) == 0
        assert validation['statement_count'] > 0
    
    def test_batch_processing_scenario(self):
        """Test batch processing of multiple files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create multiple SQL files with different content
            files_content = {
                "schema.sql": dedent("""
                    CREATE TABLE users (id serial PRIMARY KEY);
                    CREATE TABLE posts (id serial PRIMARY KEY);
                """),
                "indexes.sql": dedent("""
                    CREATE INDEX idx_users_id ON users(id);
                    CREATE INDEX idx_posts_id ON posts(id);
                """),
                "functions.sql": dedent("""
                    CREATE OR REPLACE FUNCTION get_user(user_id int)
                    RETURNS TABLE(id int) AS $$
                        SELECT id FROM users WHERE id = user_id;
                    $$ LANGUAGE sql;
                """),
                "migrations/001_init.sql": dedent("""
                    CREATE TABLE migrations (
                        id serial PRIMARY KEY,
                        name text NOT NULL
                    );
                """)
            }
            
            # Create files
            for filename, content in files_content.items():
                file_path = temp_path / filename
                file_path.parent.mkdir(exist_ok=True)
                file_path.write_text(content)
            
            # Process all files
            transformer = SQLTransformer()
            results = {}
            
            from pg_idempotent.utils.file_utils import FileOperations
            sql_files = FileOperations.find_sql_files(temp_path, recursive=True)
            
            for sql_file in sql_files:
                result = transformer.transform_file(str(sql_file))
                results[sql_file.name] = result
            
            # Verify all files were processed successfully
            assert all(r.success for r in results.values())
            assert len(results) == 4
            
            # Check specific transformations
            assert results["schema.sql"].transformed_count == 2
            assert results["indexes.sql"].transformed_count == 2
            # functions.sql has CREATE OR REPLACE, might not need transformation
            assert results["001_init.sql"].transformed_count >= 1
    
    def test_real_world_migration(self):
        """Test transformation of a real-world style migration."""
        sql = dedent("""
            -- Migration: Add user authentication tables
            
            -- Create extension if not exists
            CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
            
            -- Users table
            CREATE TABLE auth.users (
                id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
                email text UNIQUE NOT NULL,
                encrypted_password text NOT NULL,
                confirmed_at timestamp,
                created_at timestamp NOT NULL DEFAULT now(),
                updated_at timestamp NOT NULL DEFAULT now()
            );
            
            -- Sessions table
            CREATE TABLE auth.sessions (
                id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
                user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
                token text UNIQUE NOT NULL,
                expires_at timestamp NOT NULL,
                created_at timestamp NOT NULL DEFAULT now()
            );
            
            -- Indexes
            CREATE INDEX idx_users_email ON auth.users(email);
            CREATE INDEX idx_sessions_token ON auth.sessions(token);
            CREATE INDEX idx_sessions_user_id ON auth.sessions(user_id);
            
            -- RLS Policies
            ALTER TABLE auth.users ENABLE ROW LEVEL SECURITY;
            ALTER TABLE auth.sessions ENABLE ROW LEVEL SECURITY;
            
            CREATE POLICY users_select_policy ON auth.users
                FOR SELECT
                TO authenticated
                USING (id = current_user_id());
            
            CREATE POLICY sessions_select_policy ON auth.sessions
                FOR SELECT
                TO authenticated
                USING (user_id = current_user_id());
            
            -- Functions
            CREATE OR REPLACE FUNCTION auth.current_user_id()
            RETURNS uuid AS $$
                SELECT current_setting('app.user_id')::uuid;
            $$ LANGUAGE sql SECURITY DEFINER;
            
            -- Trigger for updated_at
            CREATE OR REPLACE FUNCTION auth.update_updated_at()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = now();
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            
            CREATE TRIGGER update_users_updated_at
                BEFORE UPDATE ON auth.users
                FOR EACH ROW
                EXECUTE FUNCTION auth.update_updated_at();
        """)
        
        transformer = SQLTransformer()
        result = transformer.transform_sql(sql)
        
        assert result.success
        # CREATE EXTENSION IF NOT EXISTS and CREATE OR REPLACE are already idempotent
        assert result.transformed_count < result.statement_count
        
        # Verify the transformed SQL is valid
        validation = transformer.validate_transformed_sql(result.transformed_sql)
        assert validation['valid']
        
        # Check that schema qualification is preserved
        assert "auth.users" in result.transformed_sql
        assert "auth.sessions" in result.transformed_sql
    
    def test_performance_with_large_file(self):
        """Test performance with a large SQL file."""
        # Generate a large SQL file
        statements = []
        
        # Add many CREATE TABLE statements
        for i in range(100):
            statements.append(f"""
                CREATE TABLE table_{i} (
                    id serial PRIMARY KEY,
                    data text,
                    created_at timestamp DEFAULT now()
                );
            """)
        
        # Add indexes
        for i in range(100):
            statements.append(f"CREATE INDEX idx_table_{i}_data ON table_{i}(data);")
        
        # Add some functions
        for i in range(20):
            statements.append(f"""
                CREATE FUNCTION get_table_{i}_count()
                RETURNS bigint AS $$
                    SELECT count(*) FROM table_{i};
                $$ LANGUAGE sql;
            """)
        
        large_sql = '\n'.join(statements)
        
        transformer = SQLTransformer()
        result = transformer.transform_sql(large_sql)
        
        assert result.success
        assert result.statement_count == 220
        assert result.transformed_count == 220
        
        # Should complete in reasonable time (implicit by not timing out)
        # The transformation should handle large files efficiently
    
    def test_edge_cases(self):
        """Test various edge cases."""
        # Empty file
        transformer = SQLTransformer()
        result1 = transformer.transform_sql("")
        assert result1.success
        assert result1.statement_count == 0
        
        # Only comments
        result2 = transformer.transform_sql("-- Just comments\n/* More comments */")
        assert result2.success
        assert result2.statement_count == 0
        
        # Malformed SQL
        result3 = transformer.transform_sql("CREATE TABLE (;")
        assert len(result3.errors) > 0
        
        # Unicode content
        result4 = transformer.transform_sql("CREATE TABLE émojis (name text DEFAULT '🎉');")
        assert result4.success
        assert "émojis" in result4.transformed_sql
        assert "🎉" in result4.transformed_sql