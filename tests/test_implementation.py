#!/usr/bin/env python3
"""Test script for the pg-idempotent implementation."""

import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rich.console import Console
from rich.syntax import Syntax

from pg_idempotent.transformer.transformer import SQLTransformer

console = Console()


def test_basic_transformation():
    """Test basic SQL transformation."""
    console.print("\n[bold cyan]Testing Basic Transformation[/bold cyan]")

    sql = """
CREATE TYPE user_status AS ENUM ('active', 'inactive');
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    status user_status DEFAULT 'active'
);
CREATE INDEX idx_users_email ON users(email);
"""

    transformer = SQLTransformer()
    result = transformer.transform_sql(sql)

    if result.success:
        console.print("[green]✓[/green] Transformation successful!")
        console.print(f"  Statements: {result.statement_count}")
        console.print(f"  Transformed: {result.transformed_count}")

        console.print("\n[bold]Transformed SQL:[/bold]")
        syntax = Syntax(result.transformed_sql, "sql", theme="monokai", line_numbers=True)
        console.print(syntax)
    else:
        console.print(f"[red]✗[/red] Transformation failed: {result.error}")


def test_complex_features():
    """Test complex PostgreSQL features."""
    console.print("\n[bold cyan]Testing Complex Features[/bold cyan]")

    sql = """
-- RLS Policy
CREATE POLICY user_policy ON users
    FOR ALL
    USING (id = current_user_id())
    WITH CHECK (id = current_user_id());

-- Function with dollar quotes
CREATE FUNCTION update_timestamp() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Grant statement
GRANT SELECT, INSERT ON TABLE users TO app_user;
"""

    transformer = SQLTransformer()
    result = transformer.transform_sql(sql)

    if result.success:
        console.print("[green]✓[/green] Complex features handled!")
        console.print("\n[bold]Transformed SQL:[/bold]")
        syntax = Syntax(result.transformed_sql, "sql", theme="monokai", line_numbers=True)
        console.print(syntax)
    else:
        console.print(f"[red]✗[/red] Failed: {result.error}")


def test_file_transformation():
    """Test file transformation."""
    console.print("\n[bold cyan]Testing File Transformation[/bold cyan]")

    # Check if example file exists
    example_file = Path("examples/complex_migration.sql")
    if not example_file.exists():
        console.print(f"[yellow]![/yellow] Example file not found: {example_file}")
        return

    transformer = SQLTransformer()
    result = transformer.transform_file(example_file)

    if result.success:
        console.print("[green]✓[/green] File transformation successful!")
        console.print(f"  Input: {result.input_file}")
        console.print(f"  Statements: {result.statement_count}")
        console.print(f"  Transformed: {result.transformed_count}")

        # Show first 1000 chars of result
        console.print("\n[bold]Preview (first 1000 chars):[/bold]")
        preview = (
            result.transformed_sql[:1000] + "..."
            if len(result.transformed_sql) > 1000
            else result.transformed_sql
        )
        syntax = Syntax(preview, "sql", theme="monokai")
        console.print(syntax)
    else:
        console.print(f"[red]✗[/red] File transformation failed: {result.error}")


def main():
    """Run all tests."""
    console.print("[bold green]PostgreSQL Idempotent Migration Tool - Test Suite[/bold green]")

    try:
        test_basic_transformation()
        test_complex_features()
        test_file_transformation()

        console.print("\n[bold green]✓ All tests completed![/bold green]")
    except Exception as e:
        console.print(f"\n[bold red]✗ Test failed with error:[/bold red] {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
