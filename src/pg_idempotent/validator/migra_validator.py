"""
Schema validation using migra for idempotent transformations.

This module validates that transformations produce equivalent schemas
by comparing before and after states using the migra library.
"""

import subprocess
import tempfile
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import logging
import re

try:
    from migra import Migration
    from sqlbag import S
    MIGRA_AVAILABLE = True
except ImportError:
    MIGRA_AVAILABLE = False
    logging.warning("migra not installed. Schema validation will be limited.")

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of schema validation."""
    
    is_valid: bool
    differences: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    summary: Optional[str] = None
    
    def __post_init__(self):
        """Generate summary if not provided."""
        if not self.summary:
            if self.is_valid:
                self.summary = "Schemas are functionally equivalent"
            else:
                self.summary = f"Found {len(self.differences)} differences"
    
    @property
    def has_errors(self) -> bool:
        """Check if validation has errors."""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if validation has warnings."""
        return len(self.warnings) > 0
    
    def to_report(self) -> str:
        """Generate a detailed validation report."""
        lines = [
            "Schema Validation Report",
            "=" * 50,
            f"Status: {'VALID' if self.is_valid else 'INVALID'}",
            f"Summary: {self.summary}",
            ""
        ]
        
        if self.errors:
            lines.extend([
                "Errors:",
                "-" * 20
            ])
            for error in self.errors:
                lines.append(f"  - {error}")
            lines.append("")
        
        if self.differences:
            lines.extend([
                "Schema Differences:",
                "-" * 20
            ])
            for diff in self.differences:
                lines.append(f"  - {diff}")
            lines.append("")
        
        if self.warnings:
            lines.extend([
                "Warnings:",
                "-" * 20
            ])
            for warning in self.warnings:
                lines.append(f"  - {warning}")
        
        return '\n'.join(lines)


class MigraValidator:
    """Validate schema transformations using migra."""
    
    def __init__(self, 
                 postgres_uri: Optional[str] = None,
                 use_temp_db: bool = True):
        """
        Initialize validator.
        
        Args:
            postgres_uri: PostgreSQL connection URI
            use_temp_db: Whether to use temporary databases for validation
        """
        self.postgres_uri = postgres_uri or os.getenv('DATABASE_URL')
        self.use_temp_db = use_temp_db
        
        if not MIGRA_AVAILABLE:
            logger.warning("migra not available. Install with: pip install migra")
    
    def validate_transformation(
        self,
        original_sql: str,
        transformed_sql: str,
        ignore_whitespace: bool = True
    ) -> ValidationResult:
        """
        Validate that transformation preserves schema semantics.
        
        Args:
            original_sql: Original SQL statements
            transformed_sql: Transformed SQL statements
            ignore_whitespace: Whether to ignore whitespace differences
        
        Returns:
            ValidationResult with differences found
        """
        if not MIGRA_AVAILABLE:
            return ValidationResult(
                is_valid=False,
                errors=["migra not installed. Cannot perform validation."]
            )
        
        if not self.postgres_uri:
            return ValidationResult(
                is_valid=False,
                errors=["No PostgreSQL URI provided for validation."]
            )
        
        try:
            if self.use_temp_db:
                return self._validate_with_temp_db(
                    original_sql, transformed_sql, ignore_whitespace
                )
            else:
                return self._validate_with_migra(
                    original_sql, transformed_sql, ignore_whitespace
                )
        
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation error: {str(e)}"]
            )
    
    def _validate_with_temp_db(
        self,
        original_sql: str,
        transformed_sql: str,
        ignore_whitespace: bool
    ) -> ValidationResult:
        """Validate using temporary databases."""
        # Create temporary database names
        import uuid
        temp_id = uuid.uuid4().hex[:8]
        orig_db = f"pgidempotent_orig_{temp_id}"
        trans_db = f"pgidempotent_trans_{temp_id}"
        
        try:
            # Create temporary databases
            self._create_temp_database(orig_db)
            self._create_temp_database(trans_db)
            
            # Apply schemas
            self._apply_schema(orig_db, original_sql)
            self._apply_schema(trans_db, transformed_sql)
            
            # Compare schemas using migra
            differences = self._compare_schemas(orig_db, trans_db)
            
            # Analyze differences
            result = self._analyze_differences(differences, ignore_whitespace)
            
            return result
            
        finally:
            # Clean up temporary databases
            self._drop_temp_database(orig_db)
            self._drop_temp_database(trans_db)
    
    def _validate_with_migra(
        self,
        original_sql: str,
        transformed_sql: str,
        ignore_whitespace: bool
    ) -> ValidationResult:
        """Validate using migra directly (requires existing databases)."""
        # Write SQL to temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f1:
            f1.write(original_sql)
            orig_file = f1.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f2:
            f2.write(transformed_sql)
            trans_file = f2.name
        
        try:
            # Use migra CLI for comparison
            result = subprocess.run(
                ['migra', '--unsafe', orig_file, trans_file],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return ValidationResult(is_valid=True)
            else:
                differences = result.stdout.strip().split('\n') if result.stdout else []
                return self._analyze_differences(differences, ignore_whitespace)
                
        finally:
            os.unlink(orig_file)
            os.unlink(trans_file)
    
    def _create_temp_database(self, db_name: str):
        """Create a temporary database."""
        # Parse connection URI to get admin connection
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(self.postgres_uri)
        admin_uri = urlunparse((
            parsed.scheme,
            parsed.netloc,
            'postgres',  # Connect to postgres database
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        
        # Create database
        import psycopg2
        conn = psycopg2.connect(admin_uri)
        conn.autocommit = True
        cur = conn.cursor()
        
        try:
            cur.execute(f'CREATE DATABASE "{db_name}"')
        finally:
            cur.close()
            conn.close()
    
    def _drop_temp_database(self, db_name: str):
        """Drop a temporary database."""
        try:
            from urllib.parse import urlparse, urlunparse
            parsed = urlparse(self.postgres_uri)
            admin_uri = urlunparse((
                parsed.scheme,
                parsed.netloc,
                'postgres',
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
            
            import psycopg2
            conn = psycopg2.connect(admin_uri)
            conn.autocommit = True
            cur = conn.cursor()
            
            # Terminate connections
            cur.execute(f"""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = '{db_name}' AND pid <> pg_backend_pid()
            """)
            
            # Drop database
            cur.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
            
        except Exception as e:
            logger.warning(f"Failed to drop temp database {db_name}: {e}")
        finally:
            cur.close()
            conn.close()
    
    def _apply_schema(self, db_name: str, sql: str):
        """Apply SQL schema to a database."""
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(self.postgres_uri)
        db_uri = urlunparse((
            parsed.scheme,
            parsed.netloc,
            db_name,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        
        import psycopg2
        conn = psycopg2.connect(db_uri)
        cur = conn.cursor()
        
        try:
            cur.execute(sql)
            conn.commit()
        finally:
            cur.close()
            conn.close()
    
    def _compare_schemas(self, db1: str, db2: str) -> List[str]:
        """Compare two database schemas using migra."""
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(self.postgres_uri)
        
        uri1 = urlunparse((
            parsed.scheme,
            parsed.netloc,
            db1,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        
        uri2 = urlunparse((
            parsed.scheme,
            parsed.netloc,
            db2,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        
        # Use migra to compare
        with S(uri1) as s1, S(uri2) as s2:
            m = Migration(s1, s2)
            m.set_safety(False)
            m.add_all_changes()
            
            if m.statements:
                return m.statements
            else:
                return []
    
    def _analyze_differences(
        self,
        differences: List[str],
        ignore_whitespace: bool
    ) -> ValidationResult:
        """Analyze differences and categorize them."""
        if not differences:
            return ValidationResult(is_valid=True)
        
        significant_diffs = []
        warnings = []
        
        for diff in differences:
            if not diff.strip():
                continue
            
            # Categorize differences
            if self._is_cosmetic_difference(diff, ignore_whitespace):
                warnings.append(f"Cosmetic difference: {diff}")
            else:
                significant_diffs.append(diff)
        
        is_valid = len(significant_diffs) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            differences=significant_diffs,
            warnings=warnings,
            summary=f"Found {len(significant_diffs)} significant differences"
        )
    
    def _is_cosmetic_difference(self, diff: str, ignore_whitespace: bool) -> bool:
        """Check if a difference is cosmetic (can be ignored)."""
        # Patterns for cosmetic differences
        cosmetic_patterns = [
            r'^\s*--',  # Comments
            r'^\s*$',   # Empty lines
        ]
        
        if ignore_whitespace:
            cosmetic_patterns.extend([
                r'^\s+',    # Leading whitespace
                r'\s+$',    # Trailing whitespace
                r'\s+',     # Multiple spaces
            ])
        
        for pattern in cosmetic_patterns:
            if re.match(pattern, diff):
                return True
        
        # Check for functionally equivalent statements
        diff_lower = diff.lower().strip()
        
        # IF NOT EXISTS additions are usually safe
        if 'if not exists' in diff_lower and 'create' in diff_lower:
            return True
        
        # OR REPLACE additions are usually safe
        if 'or replace' in diff_lower and 'create' in diff_lower:
            return True
        
        return False
    
    def validate_file(
        self,
        original_file: str,
        transformed_file: str,
        ignore_whitespace: bool = True
    ) -> ValidationResult:
        """Validate transformation of SQL files."""
        try:
            with open(original_file, 'r', encoding='utf-8') as f:
                original_sql = f.read()
            
            with open(transformed_file, 'r', encoding='utf-8') as f:
                transformed_sql = f.read()
            
            return self.validate_transformation(
                original_sql,
                transformed_sql,
                ignore_whitespace
            )
            
        except FileNotFoundError as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"File not found: {str(e)}"]
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"File validation error: {str(e)}"]
            )
    
    def validate_idempotency(self, sql: str) -> ValidationResult:
        """Validate that SQL is truly idempotent by running it twice."""
        if not self.postgres_uri:
            return ValidationResult(
                is_valid=False,
                errors=["No PostgreSQL URI provided for validation."]
            )
        
        # Create temporary database
        import uuid
        temp_db = f"pgidempotent_test_{uuid.uuid4().hex[:8]}"
        
        try:
            self._create_temp_database(temp_db)
            
            # Apply SQL twice
            errors = []
            warnings = []
            
            # First application
            try:
                self._apply_schema(temp_db, sql)
            except Exception as e:
                errors.append(f"First application failed: {str(e)}")
                return ValidationResult(is_valid=False, errors=errors)
            
            # Second application (should succeed if idempotent)
            try:
                self._apply_schema(temp_db, sql)
            except Exception as e:
                errors.append(f"Second application failed: {str(e)}")
                errors.append("SQL is not idempotent")
                return ValidationResult(is_valid=False, errors=errors)
            
            return ValidationResult(
                is_valid=True,
                summary="SQL is idempotent (can be run multiple times)"
            )
            
        finally:
            self._drop_temp_database(temp_db)