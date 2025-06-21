# PG Idempotent Development Guide

A comprehensive guide for package management, installation, publishing, and development workflow for the PG Idempotent project.

## Table of Contents

- [Project Structure](#project-structure)
- [Package Manager Recommendations](#package-manager-recommendations)
- [Installation Procedures](#installation-procedures)
- [PyProject.toml Overview](#pyprojecttoml-overview)
- [Development Workflow](#development-workflow)
- [Publishing Procedures](#publishing-procedures)
- [GitHub Actions Workflows](#github-actions-workflows)
- [Complete Release Process](#complete-release-process)
- [Package Installation Verification](#package-installation-verification)

## Project Structure

```
pg-idempotent/
├── .copier-answers.yml
├── .devcontainer/
│   └── devcontainer.json
├── .dockerignore
├── .github/
│   ├── dependabot.yml
│   └── workflows/
│       ├── publish.yml
│       └── test.yml
├── .gitignore
├── .pre-commit-config.yaml
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── README.md
├── src/
│   └── pg_idempotent/
│       ├── __init__.py
│       └── cli.py
└── tests/
    ├── __init__.py
    ├── test_cli.py
    └── test_import.py
```

## Package Manager Recommendations

This project is designed to work with modern Python package managers, with the following priority order:

### 1. **UV** (Recommended)
- Fast, modern Python package manager
- Best performance and dependency resolution
- Native support for `pyproject.toml`

### 2. **pip** (Fallback)
- Traditional Python package manager
- Universal compatibility
- Widely supported

### 3. **Poetry** (Alternative)
- If you prefer Poetry's approach to dependency management
- Good for complex dependency scenarios

## Installation Procedures

### For End Users (Installing the Package)

```bash
# Method 1: Using UV (fastest)
uvx pg-idempotent --help

# Method 2: Using pip (traditional)
pip install pg-idempotent

# Method 3: Install from source
pip install git+https://github.com/kivo360/pg-idempotent.git
```

### For Developers (Contributing/Development)

```bash
# Clone the repository
git clone https://github.com/kivo360/pg-idempotent.git
cd pg-idempotent

# Method 1: Using UV (recommended)
uv sync --python 3.10 --all-extras
source .venv/bin/activate
pre-commit install --install-hooks

# Method 2: Using pip + venv
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .[dev]
pre-commit install --install-hooks
```

## PyProject.toml Overview

The `pyproject.toml` file is the modern Python standard for project configuration. Here's how this one works:

### Project Configuration
```toml
[project]
name = "pg-idempotent"
version = "0.0.0"
description = "Fixes the Idempotent issues of a sql file or folder full of files."
requires-python = ">=3.10,<4.0"
dependencies = ["typer (>=0.15.1)"]
```

### CLI Entry Point
```toml
[project.scripts]
pg-idempotent = "pg_idempotent.cli:app"
```
This creates a command-line script called `pg-idempotent` that runs the `app` object from `pg_idempotent.cli` module.

### Development Dependencies
The `[dependency-groups]` section defines development tools:
- **Testing**: pytest, coverage, pytest-mock
- **Linting**: ruff (replaces flake8, isort, etc.), mypy
- **Documentation**: pdoc
- **Version management**: commitizen
- **Task runner**: poethepoet
- **Pre-commit hooks**: pre-commit

### Tool Configurations
Each tool has its own configuration section:
- **Ruff**: Modern linter/formatter (replaces flake8, isort, black)
- **MyPy**: Type checking
- **Coverage**: Test coverage reporting
- **Pytest**: Test runner configuration
- **Commitizen**: Semantic versioning and changelog generation

## Development Workflow

### Available Tasks (using Poe the Poet)
```bash
# See all available tasks
poe

# Run tests with coverage
poe test

# Lint and format code
poe lint

# Generate documentation
poe docs --output-directory docs
```

### Manual Commands
```bash
# Run tests
pytest

# Run linting
ruff check .
ruff format .

# Type checking
mypy src/

# Run pre-commit hooks
pre-commit run --all-files
```

### Current CLI State (Template)
The current CLI is a placeholder that needs to be replaced with actual SQL processing functionality:

```python
@app.command()
def fire(name: str = "Chell") -> None:
    """Fire portal gun."""
    rprint(f"[bold red]Alert![/bold red] {name} fired [green]portal gun[/green] :boom:")
```

### Intended Functionality
The tool should:
- **Fix SQL idempotency issues** in files or folders
- **Process SQL files** to make them safe to run multiple times
- **Handle PostgreSQL-specific** idempotency patterns

Example of what the real CLI might look like:
```bash
pg-idempotent process ./migrations/
pg-idempotent fix-file schema.sql
pg-idempotent validate ./sql-files/
```

## Publishing Procedures

### 1. First-Time Setup

```bash
# Install build tools
uv add --dev build twine

# OR with pip
pip install build twine
```

### 2. Configure PyPI Authentication

```bash
# Create PyPI account at https://pypi.org/account/register/
# Create API token at https://pypi.org/manage/account/token/

# Configure authentication
echo "[pypi]" > ~/.pypirc
echo "username = __token__" >> ~/.pypirc
echo "password = pypi-YOUR_API_TOKEN_HERE" >> ~/.pypirc
```

### 3. Version Management & Publishing

This project uses **Commitizen** for semantic versioning:

```bash
# Make your changes and commit using conventional commits
git add .
git commit -m "feat: add SQL file processing functionality"

# Bump version automatically based on commits
cz bump

# This will:
# - Analyze commit messages
# - Bump version appropriately (patch/minor/major)
# - Update CHANGELOG.md
# - Create a git tag
# - Update pyproject.toml version

# Push changes and tags
git push origin main --tags
```

### 4. Manual Publishing Process

```bash
# Build the package
python -m build

# Upload to TestPyPI first (recommended)
twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ pg-idempotent

# If everything works, upload to PyPI
twine upload dist/*
```

### 5. Automated Publishing (GitHub Actions)

The project includes GitHub Actions workflows. To enable automated publishing:

1. **Add PyPI API token to GitHub Secrets**:
   - Go to your repo → Settings → Secrets and variables → Actions
   - Add secret: `PYPI_API_TOKEN` with your PyPI token

2. **Publishing happens automatically**:
   - When you push a git tag (created by `cz bump`)
   - The GitHub Action will build and publish to PyPI

## GitHub Actions Workflows

The project includes two workflows:

### `.github/workflows/test.yml`
- Runs on every push/PR
- Tests on multiple Python versions
- Runs linting, type checking, and tests

### `.github/workflows/publish.yml`
- Runs when you push a git tag
- Builds and publishes to PyPI automatically

## Complete Release Process

Here's the full workflow from development to publication:

```bash
# 1. Develop features
git checkout -b feature/sql-processing
# ... implement your SQL idempotency logic ...

# 2. Commit using conventional commits
git add .
git commit -m "feat: implement SQL file idempotency checking"
git commit -m "feat: add folder processing support"
git commit -m "docs: update README with usage examples"

# 3. Merge to main
git checkout main
git merge feature/sql-processing

# 4. Run tests and ensure quality
poe test
poe lint

# 5. Bump version and create release
cz bump

# 6. Push to trigger automated publishing
git push origin main --tags
```

## Package Installation Verification

After publishing, users can install and use your package:

```bash
# Install
pip install pg-idempotent

# Use
pg-idempotent --help
pg-idempotent process ./my-sql-files/
```

## Conventional Commits

This project follows the [Conventional Commits](https://www.conventionalcommits.org/) standard:

```bash
# Types of commits:
git commit -m "feat: add new feature"
git commit -m "fix: resolve bug in SQL parsing"
git commit -m "docs: update documentation"
git commit -m "style: format code"
git commit -m "refactor: improve code structure"
git commit -m "test: add test coverage"
git commit -m "chore: update dependencies"

# Breaking changes:
git commit -m "feat!: change CLI interface"
git commit -m "feat: add new feature

BREAKING CHANGE: CLI interface has changed"
```

## Development Environment Options

The project supports multiple development environments:

1. **⭐️ GitHub Codespaces**: One-click cloud development
2. **⭐️ VS Code Dev Container**: Containerized development environment
3. **⭐️ UV**: Local development with modern tooling
4. **VS Code Dev Container (local)**: Traditional container approach
5. **PyCharm Dev Container**: JetBrains IDE support

## Quality Assurance

The project includes comprehensive quality assurance tools:

- **Ruff**: Fast linting and formatting
- **MyPy**: Static type checking
- **Pytest**: Test framework with coverage reporting
- **Pre-commit hooks**: Automated code quality checks
- **GitHub Actions**: Continuous integration and deployment

This setup provides a professional, automated workflow that follows Python packaging best practices and makes it easy for others to install and use your package!

