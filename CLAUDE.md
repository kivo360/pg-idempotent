# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Build and Development

```bash
# Quick start - set up everything and run first test
just quickstart

# Install dependencies and set up development environment
just install

# Transform a SQL file to idempotent version
just transform examples/simple.sql
just transform input.sql output.sql

# Run the CLI directly
just run transform -i input.sql -o output.sql

# Watch files and auto-transform
just watch examples/
just watch-sql examples/
```

### Testing and Quality

```bash
# Run tests
just test

# Run tests with coverage
just test-cov

# Lint and format code (runs ruff + mypy)
just lint

# Type checking only
just typecheck

# Run pre-commit hooks
just hooks
```

### SQL Test Generation

```bash
# Generate SQL test cases using Fireworks AI
just generate-tests 100 balanced
just generate-tests-fast 100 balanced  # Parallel generation

# Benchmark optimal generation settings
just benchmark-generation

# Check available Fireworks AI models
just check-models
```

### Release Management

```bash
# Create a new release (uses commitizen)
just release patch  # or minor, major

# Build package
just build

# Publish to PyPI
just publish

# Publish to TestPyPI
just publish-test
```

## High-Level Architecture

### Core Components

1. **CLI Application** (`src/pg_idempotent/cli.py`)
   - Typer-based CLI with commands: `transform`, `check`, `preview`, `batch`
   - Rich terminal UI with progress indicators
   - Supports dry-run mode and verbose output

2. **SQL Parser** (`src/pg_idempotent/parser/`)
   - `PostgreSQLParser`: Uses pglast to parse SQL into AST
   - Handles PostgreSQL-specific syntax
   - Validates SQL syntax before transformation

3. **SQL Transformer** (`src/pg_idempotent/transformer/`)
   - `SQLTransformer`: Main transformation engine
   - `StatementTransformer`: Handles individual SQL statement transformations
   - `templates.py`: Contains SQL templates for idempotent patterns
   - Transforms various SQL statements to be safely re-runnable

4. **Utilities** (`src/pg_idempotent/utils/`)
   - File handling utilities for reading/writing SQL files
   - Path resolution and validation

### Transformation Patterns

The tool transforms SQL statements to be idempotent using patterns like:
- `CREATE TABLE` → `CREATE TABLE IF NOT EXISTS`
- `CREATE INDEX` → `CREATE INDEX IF NOT EXISTS`
- `ALTER TABLE ADD COLUMN` → Wrapped with existence checks
- `CREATE TYPE` → Wrapped with conditional logic
- `INSERT` → Can add `ON CONFLICT` clauses

### Testing Structure

- **Unit Tests**: Test individual components (parser, transformer)
- **Integration Tests**: Test full transformation pipeline
- **Generated Test Cases**: Located in `examples/generated/` with varying complexity:
  - `simple/`: Basic SQL statements
  - `medium/`: Moderate complexity
  - `complex/`: Advanced SQL features
  - `extreme/`: Edge cases and stress tests

### Development Workflow

1. The project uses modern Python tooling:
   - **UV** for fast dependency management (preferred)
   - **Ruff** for linting and formatting (replaces black, isort, flake8)
   - **MyPy** for type checking
   - **Pytest** for testing with coverage
   - **Pre-commit** hooks for code quality

2. Conventional commits are enforced:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation
   - `test:` for tests
   - `refactor:` for code improvements

3. CI/CD via GitHub Actions:
   - Tests run on push/PR
   - Automatic PyPI publishing on tagged releases

### Key Design Decisions

1. **AST-based transformation**: Uses pglast to parse SQL into AST for reliable transformations
2. **Template-based patterns**: Transformation templates are centralized in `templates.py`
3. **Streaming processing**: Supports batch processing of multiple files
4. **Rich CLI experience**: Uses Rich library for enhanced terminal output
5. **Extensible architecture**: Easy to add new transformation patterns

### Environment Requirements

- Python 3.10+ required
- PostgreSQL knowledge assumed (tool is PostgreSQL-specific)
- Fireworks AI API key needed for test generation features

## Test Suite Status

### Core Tests (91/91 passing - 100%)
- **Parser Tests**: 30 tests covering dollar-quote handling, statement classification, and parsing
- **Transformer Tests**: 12 tests for SQL transformation logic
- **CLI Tests**: 30 tests for all CLI commands and workflows
- **File Utils Tests**: 20 tests for file operations

### Integration Tests (6/13 passing - 46%)
- 7 tests failing due to implementation differences:
  - Transformer uses `$IDEMPOTENT$` tags instead of `$$`
  - Different transformation counts than expected
  - Validation method returns different structure

### Advanced Feature Tests
- **LLM Namer**: Tests written but module needs `openai` dependency
- **Schema Splitter**: Tests require `rustworkx` dependency (optional)
- **Migra Validator**: Tests require `sqlalchemy` and `migra` dependencies
- **Plugin System**: Basic implementation complete

### Dependencies
Required:
- `typer[all]`, `pglast`, `rich`, `aiohttp`, `fireworks-ai`, `requests`

Optional (for advanced features):
- `openai` - for LLM-based schema naming
- `rustworkx` - for dependency graph analysis
- `migra`, `sqlalchemy` - for schema validation