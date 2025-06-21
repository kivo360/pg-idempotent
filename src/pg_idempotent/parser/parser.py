"""
PostgreSQL AST Parser with dollar-quote preprocessing.
Handles parsing of SQL statements while preserving dollar-quoted strings.
"""

import re
from dataclasses import dataclass
from typing import ClassVar

from pglast import parse_sql
from pglast.ast import Node
from pglast.enums import NodeTag


@dataclass
class DollarQuote:
    """Represents a dollar-quoted string."""

    tag: str
    content: str
    start_pos: int
    end_pos: int
    placeholder: str


@dataclass
class ParsedStatement:
    """Represents a parsed SQL statement with metadata."""

    raw_sql: str
    ast: Node | None
    statement_type: str
    object_name: str | None
    schema_name: str | None
    dollar_quotes: list[DollarQuote]
    is_idempotent: bool = False
    can_be_wrapped: bool = True
    error: str | None = None


class DollarQuotePreprocessor:
    """Handles dollar-quoted strings in PostgreSQL."""

    def __init__(self):
        # Pattern for both tagged and anonymous dollar quotes
        # This will match $tag$...$tag$ OR $...$
        self.dollar_quote_pattern = re.compile(
            r"\$([A-Za-z_]\w*)?\$(.*?)\$\1\$", re.DOTALL | re.MULTILINE
        )
        self.placeholder_prefix = "__PGIDEMPOTENT_DQ_"

    def extract_dollar_quotes(self, sql: str) -> tuple[str, list[DollarQuote]]:
        """Extract all dollar-quoted strings and replace with placeholders."""
        quotes = []
        processed_sql = sql
        
        # Use a custom parser to find dollar quotes (both tagged and anonymous)
        i = 0
        while i < len(sql):
            if sql[i] == '$':
                # Find the tag
                tag_start = i + 1
                tag_end = tag_start
                while tag_end < len(sql) and sql[tag_end] != '$':
                    if not (sql[tag_end].isalnum() or sql[tag_end] == '_'):
                        break
                    tag_end += 1
                
                if tag_end < len(sql) and sql[tag_end] == '$':
                    # Found opening delimiter
                    tag = sql[tag_start:tag_end]
                    opening_delim = sql[i:tag_end + 1]
                    closing_delim = f"${tag}$"
                    
                    # Look for matching closing delimiter
                    content_start = tag_end + 1
                    closing_pos = sql.find(closing_delim, content_start)
                    
                    if closing_pos != -1:
                        # Found complete dollar quote
                        full_content = sql[i:closing_pos + len(closing_delim)]
                        inner_content = sql[content_start:closing_pos]
                        
                        placeholder = f"{self.placeholder_prefix}{len(quotes)}__"
                        
                        quote = DollarQuote(
                            tag=tag,
                            content=full_content,
                            start_pos=i,
                            end_pos=closing_pos + len(closing_delim),
                            placeholder=placeholder,
                        )
                        quotes.append(quote)
                        
                        # Skip past this dollar quote
                        i = closing_pos + len(closing_delim)
                        continue
                elif tag_end == tag_start:
                    # Anonymous dollar quote
                    closing_pos = sql.find('$', i + 1)
                    if closing_pos != -1:
                        # Found complete anonymous dollar quote
                        full_content = sql[i:closing_pos + 1]
                        inner_content = sql[i + 1:closing_pos]
                        
                        placeholder = f"{self.placeholder_prefix}{len(quotes)}__"
                        
                        quote = DollarQuote(
                            tag="",
                            content=full_content,
                            start_pos=i,
                            end_pos=closing_pos + 1,
                            placeholder=placeholder,
                        )
                        quotes.append(quote)
                        
                        # Skip past this dollar quote
                        i = closing_pos + 1
                        continue
            
            i += 1
        
        # Replace quotes with placeholders (from end to beginning to maintain positions)
        for quote in reversed(quotes):
            processed_sql = (
                processed_sql[:quote.start_pos] + 
                f"'{quote.placeholder}'" + 
                processed_sql[quote.end_pos:]
            )
        
        return processed_sql, quotes

    def restore_dollar_quotes(self, sql: str, quotes: list[DollarQuote]) -> str:
        """Restore dollar-quoted strings from placeholders."""
        result = sql
        for quote in quotes:
            # Replace placeholder with original content
            result = result.replace(f"'{quote.placeholder}'", quote.content)
        return result

    def generate_unique_tag(self, existing_tags: set[str], base: str = "IDEMPOTENT") -> str:
        """Generate a unique dollar-quote tag."""
        counter = 1
        tag = base
        while tag in existing_tags:
            tag = f"{base}_{counter:03d}"
            counter += 1
        return tag

    def get_existing_tags(self, sql: str) -> set[str]:
        """Get all existing dollar-quote tags in SQL."""
        tags = set()
        for match in self.dollar_quote_pattern.finditer(sql):
            tag = match.group(1)
            if tag:
                tags.add(tag)
        return tags


class SQLStatementClassifier:
    """Classifies SQL statements and extracts metadata."""

    # Statements that cannot be wrapped in DO blocks
    NON_WRAPPABLE_STATEMENTS: ClassVar[set[str]] = {
        "VACUUM",
        "COPY",
        "CREATE DATABASE",
        "CREATE TABLESPACE",
        "BEGIN",
        "COMMIT",
        "ROLLBACK",
        "SAVEPOINT",
        "RELEASE",
    }

    # Already idempotent patterns
    IDEMPOTENT_PATTERNS: ClassVar[list[re.Pattern]] = [
        re.compile(r"CREATE\s+OR\s+REPLACE", re.IGNORECASE),
        re.compile(r"DROP\s+.*\s+IF\s+EXISTS", re.IGNORECASE),
        re.compile(r"ALTER\s+.*\s+IF\s+NOT\s+EXISTS", re.IGNORECASE),
        re.compile(r"DO\s+\$", re.IGNORECASE),  # Already in DO block
    ]

    @classmethod
    def classify_statement(cls, ast: Node, raw_sql: str) -> dict[str, any]:
        """Classify a statement and extract metadata."""
        result = {
            "type": "UNKNOWN",
            "object_name": None,
            "schema_name": None,
            "is_idempotent": False,
            "can_be_wrapped": True,
        }

        # Check if already idempotent
        for pattern in cls.IDEMPOTENT_PATTERNS:
            if pattern.search(raw_sql):
                result["is_idempotent"] = True
                break

        # Check if non-wrappable - do this early for all statements
        sql_upper = raw_sql.strip().upper()
        first_words = sql_upper.split()[:2] if sql_upper else []
        
        if first_words:
            # Check single word statements
            if first_words[0] in cls.NON_WRAPPABLE_STATEMENTS:
                result["can_be_wrapped"] = False
                result["type"] = first_words[0]
            # Check two-word statements like "CREATE DATABASE"
            elif len(first_words) >= 2:
                two_word_stmt = f"{first_words[0]} {first_words[1]}"
                if two_word_stmt in cls.NON_WRAPPABLE_STATEMENTS:
                    result["can_be_wrapped"] = False
                    result["type"] = two_word_stmt

        # Extract statement type and metadata from AST
        if ast and hasattr(ast, "stmt"):
            stmt = ast.stmt
            stmt_type = type(stmt).__name__

            if stmt_type == "CreateStmt":
                result["type"] = "CREATE_TABLE"
                result["object_name"] = stmt.relation.relname
                result["schema_name"] = getattr(stmt.relation, "schemaname", None)

            elif stmt_type == "CreateEnumStmt":
                result["type"] = "CREATE_TYPE"
                if stmt.typeName:
                    result["object_name"] = stmt.typeName[-1].sval

            elif stmt_type == "CreateFunctionStmt":
                result["type"] = "CREATE_FUNCTION"
                if stmt.funcname:
                    result["object_name"] = stmt.funcname[-1].sval
                # CREATE OR REPLACE FUNCTION is idempotent
                if getattr(stmt, 'replace', False):
                    result["is_idempotent"] = True

            elif stmt_type == "IndexStmt":
                result["type"] = "CREATE_INDEX"
                result["object_name"] = getattr(stmt, 'idxname', None)

            elif stmt_type == "CreatePolicyStmt":
                result["type"] = "CREATE_POLICY"
                result["object_name"] = getattr(stmt, 'policy_name', None)

            elif stmt_type == "GrantStmt":
                result["type"] = "GRANT"

            elif stmt_type == "AlterTableStmt":
                result["type"] = "ALTER_TABLE"
                if stmt.relation:
                    result["object_name"] = stmt.relation.relname
                    result["schema_name"] = getattr(stmt.relation, "schemaname", None)

            elif stmt_type == "CreateTrigStmt":
                result["type"] = "CREATE_TRIGGER"
                result["object_name"] = getattr(stmt, 'trigname', None)

            elif stmt_type == "ViewStmt":
                result["type"] = "CREATE_VIEW"
                if stmt.view:
                    result["object_name"] = stmt.view.relname
                    result["schema_name"] = getattr(stmt.view, "schemaname", None)

        return result


class PostgreSQLParser:
    """Main parser for PostgreSQL statements."""

    def __init__(self):
        self.preprocessor = DollarQuotePreprocessor()
        self.classifier = SQLStatementClassifier()
    
    def parse_sql(self, sql: str) -> list[ParsedStatement]:
        """Parse SQL into individual statements with metadata."""
        return self.parse_statements(sql)

    def parse_statements(self, sql: str) -> list[ParsedStatement]:
        """Parse SQL into individual statements with metadata."""
        statements = []

        # Split by semicolons (naive split - will be improved)
        raw_statements = self._split_statements(sql)

        for raw_stmt in raw_statements:
            if not raw_stmt.strip():
                continue

            # Extract dollar quotes
            processed_sql, dollar_quotes = self.preprocessor.extract_dollar_quotes(raw_stmt)

            # Parse with pglast
            try:
                ast_list = parse_sql(processed_sql)

                for ast in ast_list:
                    # Classify statement
                    metadata = self.classifier.classify_statement(ast, raw_stmt)

                    parsed = ParsedStatement(
                        raw_sql=raw_stmt,
                        ast=ast,
                        statement_type=metadata["type"],
                        object_name=metadata["object_name"],
                        schema_name=metadata["schema_name"],
                        dollar_quotes=dollar_quotes,
                        is_idempotent=metadata["is_idempotent"],
                        can_be_wrapped=metadata["can_be_wrapped"],
                    )
                    statements.append(parsed)

            except Exception as e:
                # Handle parse errors
                parsed = ParsedStatement(
                    raw_sql=raw_stmt,
                    ast=None,
                    statement_type="UNKNOWN",
                    object_name=None,
                    schema_name=None,
                    dollar_quotes=dollar_quotes,
                    error=str(e),
                )
                statements.append(parsed)

        return statements

    def _split_statements(self, sql: str) -> list[str]:
        """Split SQL into individual statements, respecting dollar quotes and comments."""
        statements = []
        current_statement = []
        
        # Use a more sophisticated approach with character-by-character parsing
        i = 0
        in_single_quote = False
        in_double_quote = False
        in_line_comment = False
        in_block_comment = False
        in_dollar_quote = False
        dollar_tag = None
        
        while i < len(sql):
            char = sql[i]
            peek = sql[i + 1] if i + 1 < len(sql) else None
            
            # Handle line breaks
            if char == '\n':
                if in_line_comment:
                    in_line_comment = False
                current_statement.append(char)
                i += 1
                continue
            
            # Handle line comments
            if not in_single_quote and not in_double_quote and not in_dollar_quote and not in_block_comment:
                if char == '-' and peek == '-':
                    in_line_comment = True
                    current_statement.append(char)
                    i += 1
                    continue
            
            # Handle block comments
            if not in_single_quote and not in_double_quote and not in_dollar_quote and not in_line_comment:
                if char == '/' and peek == '*':
                    in_block_comment = True
                    current_statement.append(char)
                    i += 1
                    continue
                elif char == '*' and peek == '/' and in_block_comment:
                    in_block_comment = False
                    current_statement.append(char)
                    current_statement.append(peek)
                    i += 2
                    continue
            
            # Skip processing if we're in comments
            if in_line_comment or in_block_comment:
                current_statement.append(char)
                i += 1
                continue
            
            # Handle dollar quotes
            if not in_single_quote and not in_double_quote and char == '$':
                # Look ahead to find the complete dollar quote delimiter
                tag_start = i + 1
                tag_end = tag_start
                
                # Find end of tag (continue until we hit $, whitespace, or invalid char)
                while tag_end < len(sql):
                    if sql[tag_end] == '$':
                        # Found closing $ for the tag
                        break
                    elif sql[tag_end].isalnum() or sql[tag_end] == '_':
                        # Valid tag character
                        tag_end += 1
                    else:
                        # Invalid character for tag (like newline, space, etc.)
                        # This means it's an anonymous quote like "$\n"
                        break
                
                # Check if we found a valid dollar quote delimiter
                if tag_end < len(sql) and sql[tag_end] == '$':
                    # We found a complete dollar quote delimiter like "$tag$"
                    tag = sql[tag_start:tag_end]  # Could be empty for anonymous quotes
                    delimiter = sql[i:tag_end + 1]  # The full delimiter like "$tag$" or "$$"
                    
                    if not in_dollar_quote:
                        # Starting a dollar quote
                        in_dollar_quote = True
                        dollar_tag = tag
                        current_statement.append(delimiter)
                        i = tag_end + 1
                        continue
                    elif tag == dollar_tag:
                        # Ending the current dollar quote (tags must match exactly)
                        in_dollar_quote = False
                        dollar_tag = None
                        current_statement.append(delimiter)
                        i = tag_end + 1
                        continue
                elif tag_end == tag_start:
                    # Anonymous dollar quote (no tag) like "$\n" or "$ "
                    if not in_dollar_quote:
                        # Starting an anonymous dollar quote
                        in_dollar_quote = True
                        dollar_tag = ""  # Empty tag for anonymous quotes
                        current_statement.append('$')
                        i += 1
                        continue
                    elif dollar_tag == "":
                        # Ending an anonymous dollar quote
                        in_dollar_quote = False
                        dollar_tag = None
                        current_statement.append('$')
                        i += 1
                        continue
            
            # Handle regular quotes
            if not in_dollar_quote:
                if char == "'" and not in_double_quote:
                    # Check for escaped quotes
                    if peek == "'":
                        current_statement.append(char)
                        current_statement.append(peek)
                        i += 2
                        continue
                    in_single_quote = not in_single_quote
                elif char == '"' and not in_single_quote:
                    in_double_quote = not in_double_quote
            
            # Handle statement termination
            if (char == ';' and not in_single_quote and not in_double_quote 
                and not in_dollar_quote and not in_line_comment and not in_block_comment):
                current_statement.append(char)
                stmt = ''.join(current_statement).strip()
                if stmt:
                    statements.append(stmt)
                current_statement = []
                i += 1
                continue
            
            current_statement.append(char)
            i += 1
        
        # Add any remaining statement
        if current_statement:
            stmt = ''.join(current_statement).strip()
            if stmt:
                statements.append(stmt)
        
        return statements
