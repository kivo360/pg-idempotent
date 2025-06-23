"""PG Idempotent CLI."""

import typer
from pathlib import Path
from typing import Optional, List
from rich import print as rprint
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

from .transformer.transformer import SQLTransformer

app = typer.Typer(help="PostgreSQL Idempotent Migration Tool")
console = Console()


@app.command()
def transform(
    input_file: Path = typer.Argument(..., help="Input SQL file to transform"),
    output_file: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file for transformed SQL"),
    backup: bool = typer.Option(True, "--backup/--no-backup", help="Create backup of input file"),
    validate: bool = typer.Option(True, "--validate/--no-validate", help="Validate transformed SQL"),
    stats: bool = typer.Option(False, "--stats", help="Show transformation statistics"),
) -> None:
    """Transform SQL file to idempotent version."""
    
    if not input_file.exists():
        rprint(f"[red]Error:[/red] File not found: {input_file}")
        raise typer.Exit(1)
    
    # Create transformer
    transformer = SQLTransformer()
    
    # Show stats if requested
    if stats:
        with open(input_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        transformation_stats = transformer.get_transformation_stats(sql_content)
        _display_stats(transformation_stats)
    
    # Create backup if requested
    if backup and not output_file:
        backup_file = input_file.with_suffix(f"{input_file.suffix}.backup")
        backup_file.write_text(input_file.read_text())
        rprint(f"[green]✓[/green] Backup created: {backup_file}")
    
    # Determine output file
    if not output_file:
        output_file = input_file
    
    # Transform file
    result = transformer.transform_file(str(input_file), str(output_file))
    
    if not result.success:
        rprint(f"[red]Error:[/red] Transformation failed")
        for error in result.errors:
            rprint(f"  • {error}")
        raise typer.Exit(1)
    
    # Display results
    rprint(f"[green]✓[/green] Transformation completed")
    rprint(f"  • Processed {result.statement_count} statements")
    rprint(f"  • Transformed {result.transformed_count} statements")
    
    if result.warnings:
        rprint(f"[yellow]Warnings:[/yellow]")
        for warning in result.warnings:
            rprint(f"  • {warning}")
    
    if result.errors:
        rprint(f"[red]Errors:[/red]")
        for error in result.errors:
            rprint(f"  • {error}")
    
    # Validate if requested
    if validate:
        validation = transformer.validate_transformed_sql(result.transformed_sql)
        if not validation['valid']:
            rprint(f"[yellow]Validation issues found:[/yellow]")
            for issue in validation['issues']:
                rprint(f"  • {issue}")
        else:
            rprint(f"[green]✓[/green] Validation passed")
    
    rprint(f"[green]Output written to:[/green] {output_file}")


@app.command()
def check(
    input_file: Path = typer.Argument(..., help="SQL file to analyze"),
) -> None:
    """Analyze SQL file without transforming."""
    
    if not input_file.exists():
        rprint(f"[red]Error:[/red] File not found: {input_file}")
        raise typer.Exit(1)
    
    # Create transformer and analyze
    transformer = SQLTransformer()
    
    with open(input_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    stats = transformer.get_transformation_stats(sql_content)
    _display_stats(stats)
    
    # Parse to get detailed info
    statements = transformer.parser.parse_sql(sql_content)
    
    if statements:
        rprint(f"\n[bold]Statement Details:[/bold]")
        
        table = Table()
        table.add_column("Type", style="cyan")
        table.add_column("Object", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Notes")
        
        for stmt in statements[:10]:  # Show first 10
            status = "✓ Idempotent" if stmt.is_idempotent else "⚠ Needs Transform"
            if stmt.error:
                status = "✗ Error"
            elif not stmt.can_be_wrapped:
                status = "⚠ Cannot Wrap"
            
            notes = ""
            if stmt.error:
                notes = stmt.error
            elif not stmt.can_be_wrapped:
                notes = "Cannot be wrapped in DO block"
            
            table.add_row(
                stmt.statement_type,
                stmt.object_name or "N/A",
                status,
                notes
            )
        
        console.print(table)
        
        if len(statements) > 10:
            rprint(f"... and {len(statements) - 10} more statements")


@app.command()
def preview(
    input_file: Path = typer.Argument(..., help="SQL file to preview transformation"),
    lines: int = typer.Option(20, "--lines", "-n", help="Number of lines to show"),
) -> None:
    """Preview transformation without writing to file."""
    
    if not input_file.exists():
        rprint(f"[red]Error:[/red] File not found: {input_file}")
        raise typer.Exit(1)
    
    # Transform and show preview
    transformer = SQLTransformer()
    result = transformer.transform_file(str(input_file))
    
    if not result.success:
        rprint(f"[red]Error:[/red] Transformation failed")
        for error in result.errors:
            rprint(f"  • {error}")
        raise typer.Exit(1)
    
    # Show preview
    preview_lines = result.transformed_sql.split('\n')[:lines]
    preview_content = '\n'.join(preview_lines)
    
    syntax = Syntax(preview_content, "sql", theme="monokai", line_numbers=True)
    
    panel = Panel(
        syntax,
        title=f"Preview: {input_file.name}",
        subtitle=f"Showing first {len(preview_lines)} lines"
    )
    
    console.print(panel)
    
    if len(result.transformed_sql.split('\n')) > lines:
        total_lines = len(result.transformed_sql.split('\n'))
        rprint(f"\n[dim]... and {total_lines - lines} more lines[/dim]")


@app.command()
def batch(
    directory: Path = typer.Argument(..., help="Directory containing SQL files"),
    pattern: str = typer.Option("*.sql", "--pattern", "-p", help="File pattern to match"),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", "-o", help="Output directory"),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Search recursively"),
) -> None:
    """Transform multiple SQL files in a directory."""
    
    if not directory.exists():
        rprint(f"[red]Error:[/red] Directory not found: {directory}")
        raise typer.Exit(1)
    
    # Find SQL files
    if recursive:
        files = list(directory.rglob(pattern))
    else:
        files = list(directory.glob(pattern))
    
    if not files:
        rprint(f"[yellow]No files found matching pattern: {pattern}")
        raise typer.Exit(0)
    
    rprint(f"Found {len(files)} files to process")
    
    # Create transformer
    transformer = SQLTransformer()
    
    success_count = 0
    error_count = 0
    
    for file_path in files:
        rprint(f"\n[cyan]Processing:[/cyan] {file_path.name}")
        
        # Calculate output path
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            if recursive:
                # Preserve directory structure
                rel_path = file_path.relative_to(directory)
                out_path = output_dir / rel_path
                out_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                out_path = output_dir / file_path.name
        else:
            out_path = file_path
        
        # Transform file
        result = transformer.transform_file(str(file_path), str(out_path))
        
        if result.success:
            success_count += 1
            rprint(f"  [green]✓[/green] {result.transformed_count}/{result.statement_count} statements transformed")
        else:
            error_count += 1
            rprint(f"  [red]✗[/red] Failed")
            for error in result.errors[:2]:  # Show first 2 errors
                rprint(f"    • {error}")
    
    rprint(f"\n[bold]Summary:[/bold]")
    rprint(f"  • {success_count} files processed successfully")
    rprint(f"  • {error_count} files failed")


def _display_stats(stats: dict) -> None:
    """Display transformation statistics."""
    
    table = Table(title="Transformation Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="green")
    
    table.add_row("Total Statements", str(stats['total_statements']))
    table.add_row("Already Idempotent", str(stats['already_idempotent']))
    table.add_row("Can Transform", str(stats['transformable']))
    table.add_row("Cannot Transform", str(stats['not_transformable']))
    table.add_row("Errors", str(stats['errors']))
    
    console.print(table)
    
    if stats['by_type']:
        rprint(f"\n[bold]By Statement Type:[/bold]")
        type_table = Table()
        type_table.add_column("Type", style="cyan")
        type_table.add_column("Count", style="green")
        
        for stmt_type, count in sorted(stats['by_type'].items()):
            type_table.add_row(stmt_type, str(count))
        
        console.print(type_table)


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()