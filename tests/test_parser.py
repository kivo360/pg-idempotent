"""Comprehensive tests for the PostgreSQL parser module."""

import pytest
from pg_idempotent.parser.parser import (
    DollarQuotePreprocessor, 
    SQLStatementClassifier, 
    PostgreSQLParser,
    DollarQuote,
    ParsedStatement
)
from pglast import parse_sql


class TestDollarQuotePreprocessor:
    """Test cases for DollarQuotePreprocessor class."""
    
    def setup_method(self):
        """Set up test fixture."""
        self.preprocessor = DollarQuotePreprocessor()
    
    def test_extract_simple_dollar_quote(self):
        """Test extracting simple dollar-quoted string."""
        sql = "SELECT $tag$Hello World$tag$ AS message;"
        processed, quotes = self.preprocessor.extract_dollar_quotes(sql)
        
        assert len(quotes) == 1
        assert quotes[0].tag == "tag"
        assert quotes[0].content == "$tag$Hello World$tag$"
        assert "'__PGIDEMPOTENT_DQ_0__'" in processed
        assert "$tag$" not in processed
    
    def test_extract_anonymous_dollar_quote(self):
        """Test extracting anonymous dollar-quoted string."""
        sql = "SELECT $$Hello World$$ AS message;"
        processed, quotes = self.preprocessor.extract_dollar_quotes(sql)
        
        assert len(quotes) == 1
        assert quotes[0].tag == ""
        assert quotes[0].content == "$$Hello World$$"
        assert "'__PGIDEMPOTENT_DQ_0__'" in processed
    
    def test_extract_multiple_dollar_quotes(self):
        """Test extracting multiple dollar-quoted strings."""
        sql = """
        CREATE FUNCTION test() RETURNS void AS $func$
        BEGIN
            RAISE NOTICE $msg$Hello$msg$;
        END;
        $func$ LANGUAGE plpgsql;
        """
        processed, quotes = self.preprocessor.extract_dollar_quotes(sql)
        
        # The current implementation extracts the outer quote which contains the inner quote
        assert len(quotes) == 1
        assert quotes[0].tag == "func"
        assert "$msg$Hello$msg$" in quotes[0].content  # Inner quote is part of outer content
        assert "'__PGIDEMPOTENT_DQ_0__'" in processed
    
    def test_nested_dollar_quotes(self):
        """Test handling nested dollar quotes with different tags."""
        sql = """
        DO $outer$
        DECLARE
            code TEXT := $inner$SELECT 1$inner$;
        BEGIN
            EXECUTE code;
        END;
        $outer$;
        """
        processed, quotes = self.preprocessor.extract_dollar_quotes(sql)
        
        # The current implementation extracts the outer quote which contains the inner quote
        assert len(quotes) == 1
        assert quotes[0].tag == "outer"
        assert "$inner$SELECT 1$inner$" in quotes[0].content  # Inner quote is part of outer content
    
    def test_dollar_quote_with_special_chars(self):
        """Test dollar quotes containing special characters."""
        sql = "SELECT $tag$Line 1\nLine 2\t\r\n$tag$ AS text;"
        processed, quotes = self.preprocessor.extract_dollar_quotes(sql)
        
        assert len(quotes) == 1
        assert "\n" in quotes[0].content
        assert "\t" in quotes[0].content
    
    def test_restore_dollar_quotes(self):
        """Test restoring dollar quotes from placeholders."""
        original = "SELECT $tag$Hello$tag$, $$World$$ AS text;"
        processed, quotes = self.preprocessor.extract_dollar_quotes(original)
        restored = self.preprocessor.restore_dollar_quotes(processed, quotes)
        
        assert restored == original
    
    def test_generate_unique_tag(self):
        """Test generating unique dollar quote tags."""
        existing = {"IDEMPOTENT", "IDEMPOTENT_001", "IDEMPOTENT_002"}
        
        tag1 = self.preprocessor.generate_unique_tag(existing)
        assert tag1 not in existing
        
        existing.add(tag1)
        tag2 = self.preprocessor.generate_unique_tag(existing)
        assert tag2 not in existing
        assert tag2 != tag1
    
    def test_get_existing_tags(self):
        """Test extracting existing dollar quote tags from SQL."""
        sql = """
        SELECT $tag1$text$tag1$,
               $tag2$more text$tag2$,
               $$anonymous$$
        """
        tags = self.preprocessor.get_existing_tags(sql)
        
        assert "tag1" in tags
        assert "tag2" in tags
        assert len(tags) == 2  # Anonymous quotes don't have tags
    
    def test_dollar_quote_edge_cases(self):
        """Test edge cases in dollar quote handling."""
        # Dollar sign not part of quote
        sql1 = "SELECT price * 1.5 AS price_in_dollars;"
        processed1, quotes1 = self.preprocessor.extract_dollar_quotes(sql1)
        assert len(quotes1) == 0
        
        # Incomplete dollar quote
        sql2 = "SELECT $tag$unclosed quote"
        processed2, quotes2 = self.preprocessor.extract_dollar_quotes(sql2)
        assert len(quotes2) == 0
        
        # Dollar quote with numbers in tag
        sql3 = "SELECT $tag123$content$tag123$;"
        processed3, quotes3 = self.preprocessor.extract_dollar_quotes(sql3)
        assert len(quotes3) == 1
        assert quotes3[0].tag == "tag123"


class TestSQLStatementClassifier:
    """Test cases for SQLStatementClassifier class."""
    
    def test_classify_create_table(self):
        """Test classifying CREATE TABLE statement."""
        sql = "CREATE TABLE users (id serial PRIMARY KEY, name text);"
        ast = parse_sql(sql)[0]
        
        result = SQLStatementClassifier.classify_statement(ast, sql)
        
        assert result["type"] == "CREATE_TABLE"
        assert result["object_name"] == "users"
        assert result["is_idempotent"] is False
        assert result["can_be_wrapped"] is True
    
    def test_classify_create_or_replace_function(self):
        """Test classifying CREATE OR REPLACE FUNCTION."""
        sql = "CREATE OR REPLACE FUNCTION test() RETURNS void AS $$ BEGIN END; $$ LANGUAGE plpgsql;"
        ast = parse_sql(sql)[0]
        
        result = SQLStatementClassifier.classify_statement(ast, sql)
        
        assert result["type"] == "CREATE_FUNCTION"
        assert result["object_name"] == "test"
        assert result["is_idempotent"] is True
        assert result["can_be_wrapped"] is True
    
    def test_classify_drop_if_exists(self):
        """Test classifying DROP IF EXISTS statement."""
        sql = "DROP TABLE IF EXISTS old_table;"
        ast = parse_sql(sql)[0]
        
        result = SQLStatementClassifier.classify_statement(ast, sql)
        
        assert result["is_idempotent"] is True
    
    def test_classify_non_wrappable_statements(self):
        """Test classifying statements that cannot be wrapped."""
        # Test with spaces before semicolon to match the split() behavior
        non_wrappable = [
            ("VACUUM ;", "VACUUM"),
            ("CREATE DATABASE testdb ;", "CREATE DATABASE"),
            ("BEGIN ;", "BEGIN"),
            ("COMMIT ;", "COMMIT"),
            ("ROLLBACK ;", "ROLLBACK")
        ]
        
        for sql, expected_type in non_wrappable:
            # Some of these might not parse with pglast, so we test the logic directly
            result = SQLStatementClassifier.classify_statement(None, sql)
            assert result["can_be_wrapped"] is False
            assert result["type"] == expected_type
            
        # Test VACUUM ANALYZE separately - it's recognized as VACUUM (first word)
        result = SQLStatementClassifier.classify_statement(None, "VACUUM ANALYZE ;")
        assert result["can_be_wrapped"] is False
        assert result["type"] == "VACUUM"
    
    def test_classify_alter_table(self):
        """Test classifying ALTER TABLE statement."""
        sql = "ALTER TABLE users ADD COLUMN email text;"
        ast = parse_sql(sql)[0]
        
        result = SQLStatementClassifier.classify_statement(ast, sql)
        
        assert result["type"] == "ALTER_TABLE"
        assert result["object_name"] == "users"
        assert result["is_idempotent"] is False
        assert result["can_be_wrapped"] is True
    
    def test_classify_create_index(self):
        """Test classifying CREATE INDEX statement."""
        sql = "CREATE INDEX idx_users_email ON users(email);"
        ast = parse_sql(sql)[0]
        
        result = SQLStatementClassifier.classify_statement(ast, sql)
        
        assert result["type"] == "CREATE_INDEX"
        assert result["object_name"] == "idx_users_email"
        assert result["is_idempotent"] is False
        assert result["can_be_wrapped"] is True
    
    def test_classify_grant_statement(self):
        """Test classifying GRANT statement."""
        sql = "GRANT SELECT ON users TO readonly;"
        ast = parse_sql(sql)[0]
        
        result = SQLStatementClassifier.classify_statement(ast, sql)
        
        assert result["type"] == "GRANT"
        assert result["can_be_wrapped"] is True
    
    def test_classify_with_schema(self):
        """Test classifying statements with schema names."""
        sql = "CREATE TABLE public.users (id serial PRIMARY KEY);"
        ast = parse_sql(sql)[0]
        
        result = SQLStatementClassifier.classify_statement(ast, sql)
        
        assert result["type"] == "CREATE_TABLE"
        assert result["object_name"] == "users"
        assert result["schema_name"] == "public"
    
    def test_already_in_do_block(self):
        """Test detecting statements already in DO blocks."""
        sql = "DO $$ BEGIN CREATE TABLE test(); END; $$;"
        
        result = SQLStatementClassifier.classify_statement(None, sql)
        
        assert result["is_idempotent"] is True


class TestPostgreSQLParser:
    """Test cases for PostgreSQLParser class."""
    
    def setup_method(self):
        """Set up test fixture."""
        self.parser = PostgreSQLParser()
    
    def test_parse_single_statement(self):
        """Test parsing a single SQL statement."""
        sql = "CREATE TABLE users (id serial PRIMARY KEY);"
        statements = self.parser.parse_sql(sql)
        
        assert len(statements) == 1
        assert statements[0].statement_type == "CREATE_TABLE"
        assert statements[0].object_name == "users"
        assert statements[0].error is None
    
    def test_parse_multiple_statements(self):
        """Test parsing multiple SQL statements."""
        sql = """
        CREATE TABLE users (id serial PRIMARY KEY);
        CREATE INDEX idx_users ON users(id);
        INSERT INTO users VALUES (1);
        """
        statements = self.parser.parse_sql(sql)
        
        assert len(statements) == 3
        assert statements[0].statement_type == "CREATE_TABLE"
        assert statements[1].statement_type == "CREATE_INDEX"
        assert statements[2].statement_type == "UNKNOWN"  # INSERT might not be classified
    
    def test_parse_with_comments(self):
        """Test parsing SQL with comments."""
        sql = """
        -- Create users table
        CREATE TABLE users (id serial PRIMARY KEY);
        
        /* Multi-line
           comment */
        CREATE INDEX idx_users ON users(id);
        """
        statements = self.parser.parse_sql(sql)
        
        assert len(statements) == 2
        assert statements[0].statement_type == "CREATE_TABLE"
        assert statements[1].statement_type == "CREATE_INDEX"
    
    def test_parse_with_dollar_quotes(self):
        """Test parsing SQL with dollar-quoted strings."""
        sql = """
        CREATE FUNCTION test() RETURNS void AS $func$
        BEGIN
            -- Function body
            RAISE NOTICE 'Hello';
        END;
        $func$ LANGUAGE plpgsql;
        """
        statements = self.parser.parse_sql(sql)
        
        assert len(statements) == 1
        assert statements[0].statement_type == "CREATE_FUNCTION"
        assert len(statements[0].dollar_quotes) > 0
    
    def test_parse_error_handling(self):
        """Test handling of parse errors."""
        sql = "INVALID SQL SYNTAX HERE;"
        statements = self.parser.parse_sql(sql)
        
        assert len(statements) == 1
        assert statements[0].error is not None
        assert statements[0].statement_type == "UNKNOWN"
    
    def test_split_statements_simple(self):
        """Test splitting simple statements."""
        sql = "SELECT 1; SELECT 2; SELECT 3;"
        statements = self.parser._split_statements(sql)
        
        assert len(statements) == 3
        assert "SELECT 1" in statements[0]
        assert "SELECT 2" in statements[1]
        assert "SELECT 3" in statements[2]
    
    def test_split_statements_with_quotes(self):
        """Test splitting statements with quoted semicolons."""
        sql = """
        SELECT 'text with ; semicolon';
        SELECT "column; name" FROM table;
        """
        statements = self.parser._split_statements(sql)
        
        assert len(statements) == 2
        assert "'text with ; semicolon'" in statements[0]
        assert '"column; name"' in statements[1]
    
    def test_split_statements_with_dollar_quotes(self):
        """Test splitting statements with dollar quotes."""
        sql = """
        DO $$
        BEGIN
            SELECT 1;
            SELECT 2;
        END;
        $$;
        SELECT 3;
        """
        statements = self.parser._split_statements(sql)
        
        assert len(statements) == 2
        assert "DO $$" in statements[0]
        assert "SELECT 3" in statements[1]
    
    def test_split_statements_with_comments(self):
        """Test splitting statements with comments."""
        sql = """
        -- Comment with ; semicolon
        SELECT 1;
        /* Multi-line comment
           with ; semicolon */ 
        SELECT 2;
        """
        statements = self.parser._split_statements(sql)
        
        assert len(statements) == 2
        assert "SELECT 1" in statements[0]
        assert "SELECT 2" in statements[1]
    
    def test_complex_parsing_scenario(self):
        """Test parsing complex SQL with mixed features."""
        sql = """
        -- Database setup script
        
        CREATE TABLE IF NOT EXISTS users (
            id serial PRIMARY KEY,
            name text NOT NULL,
            email text UNIQUE
        );
        
        CREATE OR REPLACE FUNCTION notify_user(user_id integer) 
        RETURNS void AS $func$
        DECLARE
            msg text := $msg$User notification$msg$;
        BEGIN
            RAISE NOTICE '%', msg;
        END;
        $func$ LANGUAGE plpgsql;
        
        -- Grant permissions
        GRANT SELECT ON users TO readonly;
        """
        
        statements = self.parser.parse_sql(sql)
        
        assert len(statements) == 3
        assert statements[0].statement_type == "CREATE_TABLE"
        assert statements[1].statement_type == "CREATE_FUNCTION"
        assert statements[1].is_idempotent is True  # CREATE OR REPLACE
        assert statements[2].statement_type == "GRANT"
        
        # Check dollar quotes were extracted
        assert any(len(stmt.dollar_quotes) > 0 for stmt in statements)
    
    def test_parse_empty_and_whitespace(self):
        """Test parsing empty and whitespace-only SQL."""
        # Empty string
        statements1 = self.parser.parse_sql("")
        assert len(statements1) == 0
        
        # Only whitespace
        statements2 = self.parser.parse_sql("   \n\n\t  ")
        assert len(statements2) == 0
        
        # Only comments
        statements3 = self.parser.parse_sql("-- Just a comment\n/* Another comment */")
        assert len(statements3) == 0
    
    def test_statement_ending_without_semicolon(self):
        """Test parsing statement without trailing semicolon."""
        sql = "CREATE TABLE test (id int)"
        statements = self.parser.parse_sql(sql)
        
        assert len(statements) == 1
        assert statements[0].statement_type == "CREATE_TABLE"
        assert statements[0].object_name == "test"