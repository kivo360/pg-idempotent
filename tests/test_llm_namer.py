"""Tests for LLM-powered schema naming system."""
import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from pg_idempotent.naming.llm_namer import (
    LLMSchemaNamer, SmartSchemaNamer, RuleBasedNamer, NamingContext
)
from pg_idempotent.parser.parser import PostgreSQLParser
from pg_idempotent.analyzer.rustworkx_analyzer import SQLObject


class TestNamingContext:
    """Test naming context data structure."""
    
    def test_context_creation(self):
        """Test creation of naming context."""
        objects = [
            SQLObject("users", "public", "table", "CREATE TABLE users...", set(), {}),
            SQLObject("posts", "public", "table", "CREATE TABLE posts...", {"users"}, {}),
            SQLObject("user_status", "public", "type", "CREATE TYPE user_status...", set(), {})
        ]
        
        context = NamingContext(
            sql_objects=objects,
            object_types={"table", "type"},
            domain_hints="e-commerce",
            existing_names={"auth", "public"}
        )
        
        assert len(context.sql_objects) == 3
        assert "table" in context.object_types
        assert "type" in context.object_types
        assert context.domain_hints == "e-commerce"
        assert "auth" in context.existing_names
    
    def test_context_with_defaults(self):
        """Test context with default values."""
        objects = [
            SQLObject("users", "public", "table", "CREATE TABLE users...", set(), {})
        ]
        
        context = NamingContext(sql_objects=objects, object_types={"table"})
        
        assert context.domain_hints is None
        assert len(context.existing_names) == 0


class TestRuleBasedNamer:
    """Test rule-based schema naming fallback."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.namer = RuleBasedNamer()
    
    def test_single_object_type_naming(self):
        """Test naming for groups with single object type."""
        object_groups = {
            "group1": [
                SQLObject("status", "public", "type", "CREATE TYPE status...", set(), {}),
                SQLObject("role", "public", "type", "CREATE TYPE role...", set(), {})
            ],
            "group2": [
                SQLObject("users", "public", "table", "CREATE TABLE users...", set(), {}),
                SQLObject("posts", "public", "table", "CREATE TABLE posts...", set(), {})
            ]
        }
        
        result = self.namer.name_schemas(object_groups)
        
        assert result["group1"] == "foundation_types"
        assert result["group2"] == "core_tables"
    
    def test_mixed_object_type_naming(self):
        """Test naming for groups with mixed object types."""
        object_groups = {
            "group1": [
                SQLObject("users", "public", "table", "CREATE TABLE users...", set(), {}),
                SQLObject("get_user", "public", "function", "CREATE FUNCTION get_user...", set(), {}),
                SQLObject("idx_users", "public", "index", "CREATE INDEX idx_users...", set(), {})
            ]
        }
        
        result = self.namer.name_schemas(object_groups)
        
        # Should pick the most common type (tables in this case have 1, others have 1 each)
        # When tied, should pick the first one alphabetically or by some consistent rule
        assert result["group1"] in ["core_tables", "business_logic", "performance_indexes"]
    
    def test_unknown_object_type_naming(self):
        """Test naming for unknown object types."""
        object_groups = {
            "group1": [
                SQLObject("unknown_obj", "public", "unknown_type", "CREATE UNKNOWN...", set(), {})
            ]
        }
        
        result = self.namer.name_schemas(object_groups)
        
        assert result["group1"] == "custom_unknown_type"


class TestLLMSchemaNamer:
    """Test LLM-powered schema naming."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock OpenAI module
        self.mock_openai = Mock()
        
    def test_api_key_configuration(self):
        """Test API key configuration options."""
        # Test explicit API key
        with patch.dict(os.environ, {}, clear=True):
            namer = LLMSchemaNamer(api_key="test-key")
            assert namer.api_key == "test-key"
        
        # Test PG_IDEMPOTENT_API_KEY environment variable
        with patch.dict(os.environ, {"PG_IDEMPOTENT_API_KEY": "pg-key"}, clear=True):
            namer = LLMSchemaNamer()
            assert namer.api_key == "pg-key"
        
        # Test fallback to OPENAI_API_KEY
        with patch.dict(os.environ, {"OPENAI_API_KEY": "openai-key"}, clear=True):
            namer = LLMSchemaNamer()
            assert namer.api_key == "openai-key"
        
        # Test preference order (PG_IDEMPOTENT_API_KEY should win)
        with patch.dict(os.environ, {
            "PG_IDEMPOTENT_API_KEY": "pg-key",
            "OPENAI_API_KEY": "openai-key"
        }, clear=True):
            namer = LLMSchemaNamer()
            assert namer.api_key == "pg-key"
    
    def test_api_key_required(self):
        """Test that API key is required."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="API key required"):
                LLMSchemaNamer()
    
    def test_base_url_configuration(self):
        """Test base URL configuration."""
        # Test explicit base URL
        namer = LLMSchemaNamer(api_key="test", base_url="https://custom.api.com/v1")
        assert namer.base_url == "https://custom.api.com/v1"
        
        # Test environment variable
        with patch.dict(os.environ, {"PG_IDEMPOTENT_BASE_URL": "https://env.api.com/v1"}):
            namer = LLMSchemaNamer(api_key="test")
            assert namer.base_url == "https://env.api.com/v1"
        
        # Test default
        with patch.dict(os.environ, {}, clear=True):
            namer = LLMSchemaNamer(api_key="test")
            assert namer.base_url == "https://api.openai.com/v1"
    
    @patch('pg_idempotent.naming.llm_namer.openai')
    def test_generate_schema_names_success(self, mock_openai):
        """Test successful schema name generation."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = """
        user_management: Tables and functions for user authentication and profiles
        content_system: Posts, comments, and content-related functionality  
        security_layer: RLS policies and access control
        foundation_types: Core data types and enums
        """
        
        mock_openai.ChatCompletion.create.return_value = mock_response
        
        # Create test context
        objects = [
            SQLObject("users", "public", "table", "CREATE TABLE users...", set(), {}),
            SQLObject("posts", "public", "table", "CREATE TABLE posts...", {"users"}, {}),
            SQLObject("user_role", "public", "type", "CREATE TYPE user_role...", set(), {})
        ]
        
        context = NamingContext(
            sql_objects=objects,
            object_types={"table", "type"},
            domain_hints="social media platform"
        )
        
        namer = LLMSchemaNamer(api_key="test-key")
        result = namer.generate_schema_names(context)
        
        # Verify API call was made correctly
        mock_openai.ChatCompletion.create.assert_called_once()
        call_args = mock_openai.ChatCompletion.create.call_args
        
        assert call_args[1]["model"] == "gpt-4"
        assert call_args[1]["temperature"] == 0.3
        assert call_args[1]["max_tokens"] == 1000
        assert len(call_args[1]["messages"]) == 2
        assert call_args[1]["messages"][0]["role"] == "system"
        assert call_args[1]["messages"][1]["role"] == "user"
        
        # Verify response parsing
        assert "user_management" in result
        assert "content_system" in result
        assert "security_layer" in result
        assert "foundation_types" in result
        
        assert "user authentication" in result["user_management"]
        assert "Posts, comments" in result["content_system"]
    
    def test_build_naming_prompt(self):
        """Test prompt building for LLM."""
        objects = [
            SQLObject("users", "public", "table", "CREATE TABLE users (id, email)...", set(), {}),
            SQLObject("posts", "public", "table", "CREATE TABLE posts (id, user_id)...", {"users"}, {}),
            SQLObject("user_status", "public", "type", "CREATE TYPE user_status...", set(), {}),
            SQLObject("post_status", "public", "type", "CREATE TYPE post_status...", set(), {})
        ]
        
        context = NamingContext(
            sql_objects=objects,
            object_types={"table", "type"},
            domain_hints="blog platform",
            existing_names={"auth", "public", "storage"}
        )
        
        namer = LLMSchemaNamer(api_key="test-key")
        prompt = namer._build_naming_prompt(context)
        
        # Should contain object summary
        assert "TABLE: users, posts" in prompt
        assert "TYPE: user_status, post_status" in prompt
        
        # Should contain object types
        assert "table, type" in prompt
        
        # Should contain domain context
        assert "blog platform" in prompt
        
        # Should contain existing names to avoid
        assert "auth, public, storage" in prompt
    
    def test_summarize_objects(self):
        """Test object summarization for prompts."""
        objects = [
            SQLObject("users", "public", "table", "CREATE TABLE users...", set(), {}),
            SQLObject("posts", "public", "table", "CREATE TABLE posts...", set(), {}),
            SQLObject("comments", "public", "table", "CREATE TABLE comments...", set(), {}),
            SQLObject("user_role", "public", "type", "CREATE TYPE user_role...", set(), {}),
            SQLObject("get_user", "public", "function", "CREATE FUNCTION get_user...", set(), {})
        ]
        
        namer = LLMSchemaNamer(api_key="test-key")
        summary = namer._summarize_objects(objects)
        
        # Should group by type
        assert "TABLE: users, posts, comments" in summary
        assert "TYPE: user_role" in summary
        assert "FUNCTION: get_user" in summary
    
    def test_summarize_many_objects(self):
        """Test object summarization with many objects."""
        objects = []
        for i in range(10):
            objects.append(
                SQLObject(f"table_{i}", "public", "table", f"CREATE TABLE table_{i}...", set(), {})
            )
        
        namer = LLMSchemaNamer(api_key="test-key")
        summary = namer._summarize_objects(objects)
        
        # Should truncate long lists
        assert "table_0, table_1, table_2 (and 7 more)" in summary
    
    def test_parse_naming_response(self):
        """Test parsing of LLM response."""
        response = """
        user_management: Core user tables and authentication
        content_system: Posts, comments, and media handling
        security_policies: RLS and access control
        foundation_types: Base types and enums
        
        Some extra text that should be ignored
        invalid_line_without_colon
        """
        
        namer = LLMSchemaNamer(api_key="test-key")
        result = namer._parse_naming_response(response)
        
        assert len(result) == 4
        assert result["user_management"] == "Core user tables and authentication"
        assert result["content_system"] == "Posts, comments, and media handling"
        assert result["security_policies"] == "RLS and access control"
        assert result["foundation_types"] == "Base types and enums"
    
    @patch('pg_idempotent.naming.llm_namer.openai')
    def test_api_error_handling(self, mock_openai):
        """Test handling of API errors."""
        # Mock API error
        mock_openai.ChatCompletion.create.side_effect = Exception("API Error")
        
        objects = [
            SQLObject("users", "public", "table", "CREATE TABLE users...", set(), {})
        ]
        context = NamingContext(sql_objects=objects, object_types={"table"})
        
        namer = LLMSchemaNamer(api_key="test-key")
        
        with pytest.raises(Exception, match="API Error"):
            namer.generate_schema_names(context)


class TestSmartSchemaNamer:
    """Test intelligent schema namer with LLM and fallback."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.object_groups = {
            "group1": [
                SQLObject("users", "public", "table", "CREATE TABLE users...", set(), {}),
                SQLObject("profiles", "public", "table", "CREATE TABLE profiles...", set(), {})
            ],
            "group2": [
                SQLObject("user_role", "public", "type", "CREATE TYPE user_role...", set(), {}),
                SQLObject("status", "public", "type", "CREATE TYPE status...", set(), {})
            ]
        }
    
    @patch('pg_idempotent.naming.llm_namer.LLMSchemaNamer')
    def test_successful_llm_naming(self, mock_llm_class):
        """Test successful LLM naming."""
        # Mock LLM namer
        mock_llm = Mock()
        mock_llm.generate_schema_names.return_value = {
            "user_management": "User tables and profiles",
            "foundation_types": "Core data types"
        }
        mock_llm_class.return_value = mock_llm
        
        namer = SmartSchemaNamer(use_llm=True)
        
        with patch.object(namer, '_map_groups_to_names') as mock_map:
            mock_map.return_value = {"group1": "user_management", "group2": "foundation_types"}
            
            result = namer.name_schemas(self.object_groups, domain_hints="social app")
            
            assert result["group1"] == "user_management"
            assert result["group2"] == "foundation_types"
            
            # Verify LLM was called with correct context
            mock_llm.generate_schema_names.assert_called_once()
            call_args = mock_llm.generate_schema_names.call_args[0][0]
            assert len(call_args.sql_objects) == 4  # 2 + 2 objects
            assert call_args.domain_hints == "social app"
    
    @patch('pg_idempotent.naming.llm_namer.LLMSchemaNamer')
    def test_llm_failure_with_fallback(self, mock_llm_class):
        """Test fallback to rule-based naming when LLM fails."""
        # Mock LLM namer that fails
        mock_llm = Mock()
        mock_llm.generate_schema_names.side_effect = Exception("API Error")
        mock_llm_class.return_value = mock_llm
        
        namer = SmartSchemaNamer(use_llm=True, fallback_to_rules=True)
        result = namer.name_schemas(self.object_groups)
        
        # Should fall back to rule-based naming
        assert result["group1"] == "core_tables"
        assert result["group2"] == "foundation_types"
    
    @patch('pg_idempotent.naming.llm_namer.LLMSchemaNamer')
    def test_llm_failure_without_fallback(self, mock_llm_class):
        """Test error propagation when fallback is disabled."""
        # Mock LLM namer that fails
        mock_llm = Mock()
        mock_llm.generate_schema_names.side_effect = Exception("API Error")
        mock_llm_class.return_value = mock_llm
        
        namer = SmartSchemaNamer(use_llm=True, fallback_to_rules=False)
        
        with pytest.raises(Exception, match="API Error"):
            namer.name_schemas(self.object_groups)
    
    def test_llm_disabled(self):
        """Test operation with LLM disabled."""
        namer = SmartSchemaNamer(use_llm=False)
        result = namer.name_schemas(self.object_groups)
        
        # Should use rule-based naming directly
        assert result["group1"] == "core_tables"
        assert result["group2"] == "foundation_types"
    
    def test_map_groups_to_names(self):
        """Test mapping of object groups to LLM-suggested names."""
        llm_names = {
            "user_management": "User accounts and profiles",
            "content_system": "Posts and media",
            "foundation": "Base types and utilities"
        }
        
        namer = SmartSchemaNamer(use_llm=False)
        result = namer._map_groups_to_names(self.object_groups, llm_names)
        
        # Should map based on content analysis or simple assignment
        # This is a placeholder test - the actual mapping logic would be more sophisticated
        assert len(result) == len(self.object_groups)
        for group_key in self.object_groups.keys():
            assert group_key in result


class TestIntegrationWithSchemaAnalysis:
    """Test integration with schema analysis components."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = PostgreSQLParser()
    
    def test_end_to_end_naming_workflow(self):
        """Test complete workflow from SQL to named schemas."""
        sql = """
        -- User management
        CREATE TYPE user_role AS ENUM ('admin', 'user', 'moderator');
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE,
            role user_role DEFAULT 'user'
        );
        CREATE TABLE user_profiles (
            user_id INTEGER REFERENCES users(id),
            display_name VARCHAR(100),
            bio TEXT
        );
        
        -- Content system
        CREATE TABLE posts (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            title VARCHAR(255),
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE comments (
            id SERIAL PRIMARY KEY,
            post_id INTEGER REFERENCES posts(id),
            user_id INTEGER REFERENCES users(id),
            content TEXT
        );
        
        -- Security
        ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
        CREATE POLICY posts_policy ON posts FOR ALL USING (user_id = current_user_id());
        
        ALTER TABLE comments ENABLE ROW LEVEL SECURITY;  
        CREATE POLICY comments_policy ON comments FOR ALL USING (user_id = current_user_id());
        """
        
        # Parse statements
        statements = self.parser.parse_sql(sql)
        assert len(statements) > 0
        
        # Convert to SQLObjects for naming
        sql_objects = []
        for stmt in statements:
            if stmt.object_name:
                sql_objects.append(SQLObject(
                    name=stmt.object_name,
                    schema=stmt.schema_name or "public",
                    object_type=stmt.statement_type.replace("CREATE_", "").lower(),
                    raw_sql=stmt.raw_sql,
                    dependencies=set(),
                    metadata={}
                ))
        
        # Group objects by logical categories (simplified)
        object_groups = {
            "user_group": [obj for obj in sql_objects if "user" in obj.name.lower()],
            "content_group": [obj for obj in sql_objects if obj.name in ["posts", "comments"]],
            "security_group": [obj for obj in sql_objects if "policy" in obj.raw_sql.lower()],
            "types_group": [obj for obj in sql_objects if obj.object_type == "type"]
        }
        
        # Filter empty groups
        object_groups = {k: v for k, v in object_groups.items() if v}
        
        # Test rule-based naming
        rule_namer = RuleBasedNamer()
        rule_result = rule_namer.name_schemas(object_groups)
        
        assert len(rule_result) > 0
        for group_name, schema_name in rule_result.items():
            assert schema_name is not None
            assert len(schema_name) > 0
    
    @patch('pg_idempotent.naming.llm_namer.openai')
    def test_realistic_llm_naming_scenario(self, mock_openai):
        """Test realistic LLM naming scenario with complex schema."""
        # Mock realistic LLM response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = """
        user_authentication: User accounts, roles, and authentication data
        content_management: Posts, comments, and user-generated content
        security_framework: Row-level security policies and access controls
        foundation_types: Core data types and enumerations
        """
        mock_openai.ChatCompletion.create.return_value = mock_response
        
        # Create complex object structure
        objects = [
            # User management objects
            SQLObject("users", "public", "table", "CREATE TABLE users...", set(), {}),
            SQLObject("user_profiles", "public", "table", "CREATE TABLE user_profiles...", {"users"}, {}),
            SQLObject("user_role", "public", "type", "CREATE TYPE user_role...", set(), {}),
            
            # Content objects
            SQLObject("posts", "public", "table", "CREATE TABLE posts...", {"users"}, {}),
            SQLObject("comments", "public", "table", "CREATE TABLE comments...", {"posts", "users"}, {}),
            
            # Security objects  
            SQLObject("posts_policy", "public", "policy", "CREATE POLICY posts_policy...", {"posts"}, {}),
            SQLObject("comments_policy", "public", "policy", "CREATE POLICY comments_policy...", {"comments"}, {})
        ]
        
        context = NamingContext(
            sql_objects=objects,
            object_types={"table", "type", "policy"},
            domain_hints="social media platform"
        )
        
        namer = LLMSchemaNamer(api_key="test-key")
        result = namer.generate_schema_names(context)
        
        # Verify meaningful schema names were generated
        assert "user_authentication" in result
        assert "content_management" in result  
        assert "security_framework" in result
        assert "foundation_types" in result
        
        # Verify descriptions are meaningful
        assert "authentication" in result["user_authentication"]
        assert "content" in result["content_management"]
        assert "security" in result["security_framework"]
        assert "types" in result["foundation_types"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])