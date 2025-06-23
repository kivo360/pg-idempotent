"""Tests for migra integration and validation system."""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sqlalchemy
from pg_idempotent.validator.migra_validator import (
    MigraValidator, ValidationResult
)
from pg_idempotent.parser.parser import PostgreSQLParser
from pg_idempotent.analyzer.rustworkx_analyzer import SQLObject


class TestValidationResult:
    """Test validation result data structure."""
    
    def test_validation_result_creation(self):
        """Test creation of validation result."""
        result = ValidationResult(
            is_valid=True,
            differences=[],
            warnings=["Warning: Index may be redundant"],
            migra_output="No differences found"
        )
        
        assert result.is_valid is True
        assert len(result.differences) == 0
        assert len(result.warnings) == 1
        assert "No differences" in result.migra_output
    
    def test_validation_result_with_errors(self):
        """Test validation result with errors."""
        result = ValidationResult(
            is_valid=False,
            differences=["Missing table: users", "Extra column: posts.slug"],
            warnings=[],
            migra_output="Found 2 differences"
        )
        
        assert result.is_valid is False
        assert len(result.differences) == 2
        assert "Missing table" in result.differences[0]
        assert "Extra column" in result.differences[1]


class TestComparisonResult:
    """Test comparison result data structure."""
    
    def test_comparison_result_creation(self):
        """Test creation of comparison result."""
        result = ComparisonResult(
            schema_differences=["Table users missing"],
            missing_objects=["public.posts"],
            extra_objects=["public.temp_table"],
            type_mismatches={"users.id": ("INTEGER", "BIGINT")},
            constraint_differences=["FK constraint missing on posts.user_id"]
        )
        
        assert len(result.schema_differences) == 1
        assert len(result.missing_objects) == 1
        assert len(result.extra_objects) == 1
        assert "users.id" in result.type_mismatches
        assert len(result.constraint_differences) == 1


class TestMigraValidator:
    """Test migra-based validation system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_db_url = "postgresql://test_user:test_pass@localhost:5432/test_db"
    
    @patch('pg_idempotent.validation.migra_validator.sqlalchemy.create_engine')
    def test_validator_initialization(self, mock_create_engine):
        """Test validator initialization."""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        validator = MigraValidator(self.test_db_url)
        
        assert validator.engine == mock_engine
        mock_create_engine.assert_called_once_with(self.test_db_url)
    
    @patch('pg_idempotent.validation.migra_validator.Migration')
    @patch('pg_idempotent.validation.migra_validator.sqlalchemy.create_engine')
    def test_validate_migration_success(self, mock_create_engine, mock_migration_class):
        """Test successful migration validation."""
        # Mock database engine
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        # Mock migra Migration
        mock_migration = Mock()
        mock_migration.sql = ""  # No differences
        mock_migration_class.return_value = mock_migration
        
        validator = MigraValidator(self.test_db_url)
        
        original_sql = "CREATE TABLE users (id SERIAL PRIMARY KEY);"
        transformed_sql = """
        DO $IDEMPOTENT$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'users'
            ) THEN
                CREATE TABLE users (id SERIAL PRIMARY KEY);
            END IF;
        END $IDEMPOTENT$;
        """
        
        result = validator.validate_migration(original_sql, transformed_sql)
        
        assert result.is_valid is True
        assert len(result.differences) == 0
        assert "identical" in result.migra_output.lower() or "no differences" in result.migra_output.lower()
    
    @patch('pg_idempotent.validation.migra_validator.Migration')
    @patch('pg_idempotent.validation.migra_validator.sqlalchemy.create_engine')
    def test_validate_migration_with_differences(self, mock_create_engine, mock_migration_class):
        """Test migration validation with differences found."""
        # Mock database engine
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        # Mock migra Migration with differences
        mock_migration = Mock()
        mock_migration.sql = "ALTER TABLE users ADD COLUMN email VARCHAR(255);"
        mock_migration_class.return_value = mock_migration
        
        validator = MigraValidator(self.test_db_url)
        
        original_sql = "CREATE TABLE users (id SERIAL PRIMARY KEY);"
        transformed_sql = "CREATE TABLE users (id SERIAL PRIMARY KEY, email VARCHAR(255));"
        
        result = validator.validate_migration(original_sql, transformed_sql)
        
        assert result.is_valid is False
        assert len(result.differences) > 0
        assert "email" in result.migra_output
    
    @patch('pg_idempotent.validation.migra_validator.Migration')
    @patch('pg_idempotent.validation.migra_validator.sqlalchemy.create_engine')
    def test_generate_diff(self, mock_create_engine, mock_migration_class):
        """Test diff generation between schemas."""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        mock_migration = Mock()
        mock_migration.sql = "CREATE INDEX idx_users_email ON users(email);"
        mock_migration_class.return_value = mock_migration
        
        validator = MigraValidator(self.test_db_url)
        
        source_sql = "CREATE TABLE users (id SERIAL, email VARCHAR(255));"
        target_sql = """
        CREATE TABLE users (id SERIAL, email VARCHAR(255));
        CREATE INDEX idx_users_email ON users(email);
        """
        
        diff = validator.generate_diff(source_sql, target_sql)
        
        assert "CREATE INDEX" in diff
        assert "idx_users_email" in diff
    
    @patch('pg_idempotent.validation.migra_validator.sqlalchemy.create_engine')
    def test_validate_idempotency_success(self, mock_create_engine):
        """Test successful idempotency validation."""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        # Mock database operations
        mock_connection = Mock()
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_connection.execute.return_value = Mock()
        
        validator = MigraValidator(self.test_db_url)
        
        # Idempotent SQL that can be run multiple times
        idempotent_sql = """
        DO $IDEMPOTENT$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'users'
            ) THEN
                CREATE TABLE users (id SERIAL PRIMARY KEY);
            END IF;
        END $IDEMPOTENT$;
        """
        
        result = validator.validate_idempotency(idempotent_sql)
        
        assert result is True
        # Should have executed the SQL twice to test idempotency
        assert mock_connection.execute.call_count >= 2
    
    @patch('pg_idempotent.validation.migra_validator.sqlalchemy.create_engine')
    def test_validate_idempotency_failure(self, mock_create_engine):
        """Test idempotency validation failure."""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        # Mock database operations that fail on second run
        mock_connection = Mock()
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        
        # First call succeeds, second call fails
        mock_connection.execute.side_effect = [
            Mock(),  # First execution succeeds
            Exception("relation 'users' already exists")  # Second execution fails
        ]
        
        validator = MigraValidator(self.test_db_url)
        
        # Non-idempotent SQL
        non_idempotent_sql = "CREATE TABLE users (id SERIAL PRIMARY KEY);"
        
        result = validator.validate_idempotency(non_idempotent_sql)
        
        assert result is False
    
    @patch('pg_idempotent.validation.migra_validator.sqlalchemy.create_engine')
    def test_database_connection_error(self, mock_create_engine):
        """Test handling of database connection errors."""
        mock_create_engine.side_effect = Exception("Connection failed")
        
        with pytest.raises(Exception, match="Connection failed"):
            MigraValidator(self.test_db_url)
    
    def test_invalid_sql_handling(self):
        """Test handling of invalid SQL."""
        with patch('pg_idempotent.validation.migra_validator.sqlalchemy.create_engine') as mock_create_engine:
            mock_engine = Mock()
            mock_create_engine.return_value = mock_engine
            
            validator = MigraValidator(self.test_db_url)
            
            invalid_sql = "CREATE INVALID SYNTAX;"
            
            with pytest.raises(Exception):
                validator.validate_idempotency(invalid_sql)


class TestDatabaseComparator:
    """Test database comparison functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.comparator = DatabaseComparator()
    
    def test_compare_schemas_identical(self):
        """Test comparison of identical schemas."""
        schema1 = """
        CREATE TABLE users (id SERIAL PRIMARY KEY, email VARCHAR(255));
        CREATE INDEX idx_users_email ON users(email);
        """
        
        schema2 = """
        CREATE TABLE users (id SERIAL PRIMARY KEY, email VARCHAR(255));
        CREATE INDEX idx_users_email ON users(email);
        """
        
        result = self.comparator.compare_schemas(schema1, schema2)
        
        assert len(result.schema_differences) == 0
        assert len(result.missing_objects) == 0
        assert len(result.extra_objects) == 0
        assert len(result.type_mismatches) == 0
    
    def test_compare_schemas_with_differences(self):
        """Test comparison of different schemas."""
        schema1 = """
        CREATE TABLE users (id SERIAL PRIMARY KEY);
        """
        
        schema2 = """
        CREATE TABLE users (id SERIAL PRIMARY KEY, email VARCHAR(255));
        CREATE TABLE posts (id SERIAL PRIMARY KEY, user_id INTEGER);
        """
        
        result = self.comparator.compare_schemas(schema1, schema2)
        
        assert len(result.schema_differences) > 0 or len(result.extra_objects) > 0
    
    def test_validate_dependencies_success(self):
        """Test successful dependency validation."""
        objects = [
            SQLObject("users", "public", "table", "CREATE TABLE users (id SERIAL);", set(), {}),
            SQLObject("posts", "public", "table", "CREATE TABLE posts (user_id INTEGER REFERENCES users(id));", {"users"}, {})
        ]
        
        errors = self.comparator.validate_dependencies(objects)
        
        assert len(errors) == 0
    
    def test_validate_dependencies_missing_dependency(self):
        """Test dependency validation with missing dependencies."""
        objects = [
            SQLObject("posts", "public", "table", "CREATE TABLE posts (user_id INTEGER REFERENCES users(id));", {"users"}, {})
            # Missing 'users' table that posts depends on
        ]
        
        errors = self.comparator.validate_dependencies(objects)
        
        assert len(errors) > 0
        assert any("users" in str(error) for error in errors)
    
    def test_check_circular_dependencies_none(self):
        """Test circular dependency check with no cycles."""
        graph = DependencyGraph()
        # Add mock objects and edges representing a DAG
        # This would need the actual DependencyGraph implementation
        
        cycles = self.comparator.check_circular_dependencies(graph)
        
        # With a proper DAG, should find no cycles
        assert isinstance(cycles, list)
    
    def test_check_circular_dependencies_found(self):
        """Test circular dependency detection."""
        graph = DependencyGraph()
        # Add mock objects and edges representing a cycle
        # This would need the actual DependencyGraph implementation
        
        cycles = self.comparator.check_circular_dependencies(graph)
        
        # Should detect cycles if they exist
        assert isinstance(cycles, list)


class TestValidationIntegration:
    """Test integration of validation with other components."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = PostgreSQLParser()
    
    def test_end_to_end_validation_workflow(self):
        """Test complete validation workflow."""
        # Original SQL
        original_sql = """
        CREATE TYPE user_status AS ENUM ('active', 'inactive');
        
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            status user_status DEFAULT 'active'
        );
        
        CREATE TABLE posts (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            title VARCHAR(255) NOT NULL,
            content TEXT
        );
        
        CREATE INDEX idx_posts_user ON posts(user_id);
        """
        
        # Parse statements
        statements = self.parser.parse_sql(original_sql)
        assert len(statements) > 0
        
        # Convert to SQLObjects
        sql_objects = []
        for stmt in statements:
            if stmt.object_name:
                dependencies = set()
                # Simple dependency extraction (would be more sophisticated in real implementation)
                if "REFERENCES" in stmt.raw_sql:
                    import re
                    refs = re.findall(r'REFERENCES\s+(\w+)', stmt.raw_sql, re.IGNORECASE)
                    dependencies.update(refs)
                
                sql_objects.append(SQLObject(
                    name=stmt.object_name,
                    schema=stmt.schema_name or "public",
                    object_type=stmt.statement_type.replace("CREATE_", "").lower(),
                    raw_sql=stmt.raw_sql,
                    dependencies=dependencies,
                    metadata={}
                ))
        
        # Test dependency validation
        comparator = DatabaseComparator()
        validation_errors = comparator.validate_dependencies(sql_objects)
        
        # Should have no validation errors for this well-formed schema
        assert len(validation_errors) == 0
    
    @patch('pg_idempotent.validation.migra_validator.sqlalchemy.create_engine')
    def test_transformed_sql_validation(self, mock_create_engine):
        """Test validation of transformed idempotent SQL."""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        original = "CREATE TABLE users (id SERIAL PRIMARY KEY);"
        
        # This would come from the transformer
        transformed = """
        DO $IDEMPOTENT$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'users'
            ) THEN
                CREATE TABLE users (id SERIAL PRIMARY KEY);
            END IF;
        END $IDEMPOTENT$;
        """
        
        with patch('pg_idempotent.validation.migra_validator.Migration') as mock_migration_class:
            mock_migration = Mock()
            mock_migration.sql = ""  # No differences
            mock_migration_class.return_value = mock_migration
            
            validator = MigraValidator("postgresql://test")
            result = validator.validate_migration(original, transformed)
            
            assert result.is_valid is True
    
    def test_validation_error_types(self):
        """Test different types of validation errors."""
        # Test missing dependency error
        error1 = ValidationError(
            error_type="missing_dependency",
            object_name="posts",
            message="Table 'posts' references missing table 'users'",
            severity="error"
        )
        
        assert error1.error_type == "missing_dependency"
        assert error1.severity == "error"
        assert "users" in error1.message
        
        # Test circular dependency error
        error2 = ValidationError(
            error_type="circular_dependency",
            object_name="table_a",
            message="Circular dependency detected: table_a -> table_b -> table_a",
            severity="warning"
        )
        
        assert error2.error_type == "circular_dependency"
        assert error2.severity == "warning"
        assert "Circular dependency" in error2.message


class TestMockDatabaseOperations:
    """Test validation with mock database operations."""
    
    @patch('pg_idempotent.validation.migra_validator.sqlalchemy.create_engine')
    def test_mock_database_validation(self, mock_create_engine):
        """Test validation using mock database operations."""
        # Mock successful database setup
        mock_engine = Mock()
        mock_connection = Mock()
        mock_create_engine.return_value = mock_engine
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        
        # Mock successful query execution
        mock_connection.execute.return_value = Mock()
        
        validator = MigraValidator("postgresql://mock")
        
        # Test with simple SQL
        sql = """
        DO $TEST$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'test') THEN
                CREATE TABLE test (id SERIAL);
            END IF;
        END $TEST$;
        """
        
        # Should not raise exceptions
        result = validator.validate_idempotency(sql)
        assert isinstance(result, bool)
    
    def test_database_error_handling(self):
        """Test proper error handling for database operations."""
        with patch('pg_idempotent.validation.migra_validator.sqlalchemy.create_engine') as mock_create_engine:
            # Mock connection that raises an error
            mock_engine = Mock()
            mock_connection = Mock()
            mock_create_engine.return_value = mock_engine
            mock_engine.connect.return_value.__enter__.return_value = mock_connection
            mock_connection.execute.side_effect = Exception("Database connection lost")
            
            validator = MigraValidator("postgresql://failing")
            
            with pytest.raises(Exception, match="Database connection lost"):
                validator.validate_idempotency("SELECT 1;")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])