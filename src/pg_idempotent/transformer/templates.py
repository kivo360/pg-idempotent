"""
Idempotent transformation templates for PostgreSQL DDL statements.
"""
from typing import Dict, Optional, List, Set
from dataclasses import dataclass
from ..parser.parser import ParsedStatement, DollarQuotePreprocessor


@dataclass
class TransformationTemplate:
    """Template for transforming statements to idempotent versions."""
    check_query: str
    wrapper_template: str
    requires_schema: bool = True
    requires_name: bool = True


class IdempotentTemplates:
    """Collection of idempotent transformation templates."""
    
    TEMPLATES = {
        'CREATE_TABLE': TransformationTemplate(
            check_query="""
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = '{schema}' 
            AND table_name = '{name}'
            """,
            wrapper_template="""DO {dollar_tag}
BEGIN
    IF NOT EXISTS ({check_query}) THEN
        {statement}
    END IF;
END {dollar_tag};"""
        ),
        
        'CREATE_TYPE': TransformationTemplate(
            check_query="""
            SELECT 1 FROM pg_type 
            WHERE typname = '{name}'
            AND typnamespace = '{schema}'::regnamespace
            """,
            wrapper_template="""DO {dollar_tag}
BEGIN
    IF NOT EXISTS ({check_query}) THEN
        {statement}
    END IF;
END {dollar_tag};"""
        ),
        
        'CREATE_INDEX': TransformationTemplate(
            check_query="""
            SELECT 1 FROM pg_indexes 
            WHERE schemaname = '{schema}' 
            AND indexname = '{name}'
            """,
            wrapper_template="""DO {dollar_tag}
BEGIN
    IF NOT EXISTS ({check_query}) THEN
        {statement}
    END IF;
END {dollar_tag};"""
        ),
        
        'CREATE_POLICY': TransformationTemplate(
            check_query="""
            SELECT 1 FROM pg_policies 
            WHERE schemaname = '{schema}' 
            AND tablename = '{table}' 
            AND policyname = '{name}'
            """,
            wrapper_template="""DO {dollar_tag}
BEGIN
    IF NOT EXISTS ({check_query}) THEN
        {statement}
    END IF;
END {dollar_tag};""",
            requires_schema=True
        ),
        
        'CREATE_TRIGGER': TransformationTemplate(
            check_query="""
            SELECT 1 FROM pg_trigger 
            WHERE tgname = '{name}'
            AND tgrelid = '{schema}.{table}'::regclass
            """,
            wrapper_template="""DO {dollar_tag}
BEGIN
    IF NOT EXISTS ({check_query}) THEN
        {statement}
    END IF;
END {dollar_tag};"""
        ),
        
        'CREATE_VIEW': TransformationTemplate(
            check_query="""
            SELECT 1 FROM information_schema.views 
            WHERE table_schema = '{schema}' 
            AND table_name = '{name}'
            """,
            wrapper_template="""DO {dollar_tag}
BEGIN
    IF NOT EXISTS ({check_query}) THEN
        {statement}
    END IF;
END {dollar_tag};"""
        ),
        
        'CREATE_FUNCTION': TransformationTemplate(
            check_query="""
            SELECT 1 FROM pg_proc 
            WHERE proname = '{name}' 
            AND pronamespace = '{schema}'::regnamespace
            """,
            wrapper_template="""DO {dollar_tag}
BEGIN
    IF NOT EXISTS ({check_query}) THEN
        {statement}
    END IF;
END {dollar_tag};"""
        ),
        
        'ALTER_TABLE': TransformationTemplate(
            check_query="",  # ALTER TABLE needs special handling
            wrapper_template="""DO {dollar_tag}
BEGIN
    -- ALTER TABLE statements need custom checks based on the specific alteration
    {statement}
EXCEPTION
    WHEN duplicate_column THEN NULL;
    WHEN duplicate_object THEN NULL;
    WHEN duplicate_table THEN NULL;
END {dollar_tag};"""
        ),
        
        'GRANT': TransformationTemplate(
            check_query="""
            SELECT 1 FROM information_schema.table_privileges
            WHERE grantee = '{grantee}'
            AND table_schema = '{schema}'
            AND table_name = '{table}'
            AND privilege_type = '{privilege}'
            """,
            wrapper_template="""DO {dollar_tag}
BEGIN
    -- GRANT needs custom handling for multiple privileges
    {custom_grant_logic}
END {dollar_tag};""",
            requires_schema=True
        ),
    }
    
    @classmethod
    def get_template(cls, statement_type: str) -> Optional[TransformationTemplate]:
        """Get template for statement type."""
        return cls.TEMPLATES.get(statement_type)


class StatementTransformer:
    """Transforms SQL statements to idempotent versions."""
    
    def __init__(self):
        self.preprocessor = DollarQuotePreprocessor()
        self.templates = IdempotentTemplates()
        self._used_tags: Set[str] = set()
    
    def transform_statement(self, parsed: ParsedStatement) -> str:
        """Transform a parsed statement to idempotent version."""
        # Already idempotent or has errors
        if parsed.is_idempotent or parsed.error:
            return parsed.raw_sql
        
        # Cannot be wrapped
        if not parsed.can_be_wrapped:
            return f"-- WARNING: {parsed.statement_type} cannot be wrapped in DO block\n{parsed.raw_sql}"
        
        # Get template
        template = self.templates.get_template(parsed.statement_type)
        if not template:
            return f"-- WARNING: No template for {parsed.statement_type}\n{parsed.raw_sql}"
        
        # Extract existing dollar quote tags
        existing_tags = self.preprocessor.get_existing_tags(parsed.raw_sql)
        existing_tags.update(self._used_tags)
        
        # Generate unique tag
        dollar_tag = self.preprocessor.generate_unique_tag(existing_tags)
        self._used_tags.add(dollar_tag)
        dollar_tag = f"${dollar_tag}$"
        
        # Prepare template values
        schema = parsed.schema_name or 'public'
        
        # Build check query
        check_query = template.check_query.format(
            schema=schema,
            name=parsed.object_name,
            table='',  # Will be extracted for policies/triggers
            grantee='',  # Will be extracted for grants
            privilege=''  # Will be extracted for grants
        ).strip()
        
        # Special handling for different statement types
        if parsed.statement_type == 'GRANT':
            return self._transform_grant(parsed, template, dollar_tag)
        elif parsed.statement_type == 'ALTER_TABLE':
            return self._transform_alter_table(parsed, template, dollar_tag)
        elif parsed.statement_type == 'CREATE_FUNCTION':
            return self._transform_function(parsed, dollar_tag)
        
        # Standard transformation
        transformed = template.wrapper_template.format(
            dollar_tag=dollar_tag,
            check_query=check_query,
            statement=parsed.raw_sql.rstrip(';')
        )
        
        return transformed
    
    def _transform_grant(self, parsed: ParsedStatement, template: TransformationTemplate, 
                        dollar_tag: str) -> str:
        """Special handling for GRANT statements."""
        # Extract grant details from raw SQL
        # This is simplified - production would use AST
        import re
        
        grant_match = re.search(
            r'GRANT\s+(.*?)\s+ON\s+(?:TABLE\s+)?(\S+)\s+TO\s+(\S+)',
            parsed.raw_sql,
            re.IGNORECASE
        )
        
        if not grant_match:
            return parsed.raw_sql
        
        privileges = [p.strip() for p in grant_match.group(1).split(',')]
        table = grant_match.group(2)
        grantee = grant_match.group(3)
        
        # Build custom grant logic
        checks = []
        grants = []
        
        for privilege in privileges:
            check = f"""
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_privileges
        WHERE grantee = '{grantee}'
        AND table_schema = 'public'
        AND table_name = '{table}'
        AND privilege_type = '{privilege.upper()}'
    ) THEN
        GRANT {privilege} ON TABLE {table} TO {grantee};
    END IF;"""
            checks.append(check)
        
        custom_logic = '\n'.join(checks)
        
        return f"""DO {dollar_tag}
BEGIN{custom_logic}
END {dollar_tag};"""
    
    def _transform_alter_table(self, parsed: ParsedStatement, template: TransformationTemplate,
                              dollar_tag: str) -> str:
        """Special handling for ALTER TABLE statements."""
        # Use exception handling approach
        return template.wrapper_template.format(
            dollar_tag=dollar_tag,
            statement=parsed.raw_sql.rstrip(';')
        )
    
    def _transform_function(self, parsed: ParsedStatement, dollar_tag: str) -> str:
        """Special handling for CREATE FUNCTION statements."""
        # Functions with CREATE OR REPLACE are already idempotent
        if 'CREATE OR REPLACE' in parsed.raw_sql.upper():
            return parsed.raw_sql
        
        # For regular CREATE FUNCTION, wrap it
        schema = parsed.schema_name or 'public'
        
        return f"""DO {dollar_tag}
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_proc 
        WHERE proname = '{parsed.object_name}' 
        AND pronamespace = '{schema}'::regnamespace
    ) THEN
        {parsed.raw_sql.rstrip(';')}
    END IF;
END {dollar_tag};"""
    
    def transform_statements(self, statements: List[ParsedStatement]) -> List[str]:
        """Transform a list of statements."""
        self._used_tags.clear()
        return [self.transform_statement(stmt) for stmt in statements]