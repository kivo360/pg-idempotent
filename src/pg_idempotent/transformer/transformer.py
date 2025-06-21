"""
Main transformer module that ties everything together.
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from ..parser.parser import PostgreSQLParser, ParsedStatement
from .templates import StatementTransformer


@dataclass
class TransformationResult:
    """Result of SQL transformation."""
    success: bool
    transformed_sql: str
    statement_count: int
    transformed_count: int
    errors: List[str]
    warnings: List[str]
    
    def __post_init__(self):
        """Initialize empty lists if None."""
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class SQLTransformer:
    """Main SQL transformer class."""
    
    def __init__(self):
        self.parser = PostgreSQLParser()
        self.statement_transformer = StatementTransformer()
    
    def transform_sql(self, sql: str) -> TransformationResult:
        """Transform SQL to idempotent version."""
        if not sql.strip():
            return TransformationResult(
                success=True,
                transformed_sql="",
                statement_count=0,
                transformed_count=0,
                errors=[],
                warnings=[]
            )
        
        try:
            # Parse SQL
            statements = self.parser.parse_sql(sql)
            
            # Transform statements
            transformed_statements = self.statement_transformer.transform_statements(statements)
            
            # Join transformed statements
            transformed_sql = '\n\n'.join(transformed_statements)
            
            # Count transformations
            transformed_count = sum(
                1 for stmt in statements 
                if not stmt.is_idempotent and stmt.can_be_wrapped and not stmt.error
            )
            
            # Collect errors and warnings
            errors = [stmt.error for stmt in statements if stmt.error]
            warnings = []
            
            return TransformationResult(
                success=True,
                transformed_sql=transformed_sql,
                statement_count=len(statements),
                transformed_count=transformed_count,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            return TransformationResult(
                success=False,
                transformed_sql=sql,
                statement_count=0,
                transformed_count=0,
                errors=[f"Transformation failed: {str(e)}"],
                warnings=[]
            )
    
    def transform_file(self, input_file: str, output_file: Optional[str] = None) -> TransformationResult:
        """Transform SQL file to idempotent version."""
        try:
            # Read input file
            with open(input_file, 'r', encoding='utf-8') as f:
                sql = f.read()
            
            # Transform SQL
            result = self.transform_sql(sql)
            
            # Write to output file if specified
            if output_file and result.success:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result.transformed_sql)
            
            return result
            
        except FileNotFoundError:
            return TransformationResult(
                success=False,
                transformed_sql="",
                statement_count=0,
                transformed_count=0,
                errors=[f"File not found: {input_file}"],
                warnings=[]
            )
        except Exception as e:
            return TransformationResult(
                success=False,
                transformed_sql="",
                statement_count=0,
                transformed_count=0,
                errors=[f"File processing failed: {str(e)}"],
                warnings=[]
            )
    
    def validate_transformed_sql(self, transformed_sql: str) -> Dict[str, Any]:
        """Validate transformed SQL for common issues."""
        validation_result = {
            'valid': True,
            'issues': [],
            'suggestions': []
        }
        
        # Check for unbalanced dollar quotes
        dollar_quotes = []
        lines = transformed_sql.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Simple dollar quote detection
            import re
            matches = re.findall(r'\$[^$]*\$', line)
            for match in matches:
                if match in dollar_quotes:
                    dollar_quotes.remove(match)
                else:
                    dollar_quotes.append(match)
        
        if dollar_quotes:
            validation_result['valid'] = False
            validation_result['issues'].append(
                f"Unbalanced dollar quotes found: {', '.join(dollar_quotes)}"
            )
        
        # Check for proper DO block structure
        do_blocks = re.findall(r'DO\s+\$[^$]*\$.*?END\s+\$[^$]*\$', transformed_sql, re.DOTALL | re.IGNORECASE)
        if 'DO $' in transformed_sql and not do_blocks:
            validation_result['issues'].append("Malformed DO blocks detected")
        
        return validation_result
    
    def get_transformation_stats(self, sql: str) -> Dict[str, int]:
        """Get statistics about what would be transformed."""
        statements = self.parser.parse_sql(sql)
        
        stats = {
            'total_statements': len(statements),
            'already_idempotent': sum(1 for stmt in statements if stmt.is_idempotent),
            'transformable': sum(1 for stmt in statements if stmt.can_be_wrapped and not stmt.error),
            'not_transformable': sum(1 for stmt in statements if not stmt.can_be_wrapped),
            'errors': sum(1 for stmt in statements if stmt.error)
        }
        
        # Count by statement type
        type_counts = {}
        for stmt in statements:
            type_counts[stmt.statement_type] = type_counts.get(stmt.statement_type, 0) + 1
        
        stats['by_type'] = type_counts
        
        return stats