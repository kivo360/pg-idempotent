# PostgreSQL Idempotent Migration Tool - Justfile
# https://github.com/casey/just

# Default recipe to display help
default:
    @just --list

# Quick start - set up everything and run first test
quickstart: install test-example
    @echo "✅ Quick start complete! Try: just transform examples/simple.sql"

# Install dependencies and set up development environment
install:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "🔧 Setting up development environment..."
    if command -v uv &> /dev/null; then
        echo "📦 Using UV (fast mode)"
        uv sync --all-extras
    else
        echo "📦 Using pip"
        python -m venv .venv || python3 -m venv .venv
        source .venv/bin/activate
        pip install -e ".[dev]"
    fi
    pre-commit install --install-hooks
    echo "✅ Development environment ready"

# Run the CLI
run *args:
    python -m pg_idempotent {{args}}

# Transform a SQL file (shorthand)
transform input output="":
    #!/usr/bin/env bash
    if [ -z "{{output}}" ]; then
        python -m pg_idempotent transform -i {{input}} --dry-run
    else
        python -m pg_idempotent transform -i {{input}} -o {{output}}
    fi

# Run tests
test:
    pytest -v

# Run tests with coverage
test-cov:
    pytest --cov --cov-report=html
    @echo "📊 Coverage report: htmlcov/index.html"

# Test with example file
test-example:
    @echo "🧪 Testing transformation on example..."
    @mkdir -p examples
    @echo "CREATE TYPE status AS ENUM ('active', 'inactive');" > examples/simple.sql
    @echo "CREATE TABLE users (id SERIAL PRIMARY KEY, status status);" >> examples/simple.sql
    python -m pg_idempotent transform -i examples/simple.sql --dry-run

# Lint and format code
lint:
    ruff check . --fix
    ruff format .
    mypy src/

# Type check
typecheck:
    mypy src/

# Run pre-commit hooks
hooks:
    pre-commit run --all-files

# Clean up generated files
clean:
    rm -rf dist/ build/ *.egg-info
    rm -rf .pytest_cache/ htmlcov/ .coverage
    rm -rf .mypy_cache/ .ruff_cache/
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete

# Build package
build: clean
    python -m build

# Create a new release (bump version)
release type="patch":
    #!/usr/bin/env bash
    set -euo pipefail
    echo "📦 Creating {{type}} release..."
    cz bump --{{type}}
    echo "✅ Release created. Run 'git push --follow-tags' to publish"

# Publish to PyPI
publish: build
    #!/usr/bin/env bash
    set -euo pipefail
    echo "📤 Publishing to PyPI..."
    python -m twine upload dist/*
    echo "✅ Published! Install with: pip install pg-idempotent"

# Publish to TestPyPI
publish-test: build
    #!/usr/bin/env bash
    set -euo pipefail
    echo "📤 Publishing to TestPyPI..."
    python -m twine upload --repository testpypi dist/*
    echo "✅ Published to TestPyPI!"

# Watch files and auto-transform
watch path="examples":
    #!/usr/bin/env bash
    echo "👀 Watching {{path}} for changes..."
    watchexec \
        --exts sql,py,ts,js,json,yaml,yml,toml,md,rst,txt,ini,cfg,conf,env \
        --recursive \
        --clear \
        --postpone \
        -- just transform-watch {{path}}

# Run Shrimpy task by name
shrimpy task:
    shrimpy execute "{{task}}"

# List all Shrimpy tasks
shrimpy-list:
    shrimpy list

# Initialize Shrimpy tasks
shrimpy-init:
    @mkdir -p .shrimpy
    @cp .shrimpy/tasks.json.template .shrimpy/tasks.json
    @echo "✅ Shrimpy tasks initialized"

# Development server with hot reload
dev:
    watchexec \
        --exts py,sql,toml,yaml,json \
        --watch src \
        --watch examples \
        --restart \
        --clear \
        -- python -m pg_idempotent serve

# Helper for watch command - transform when SQL files change
transform-watch path:
    #!/usr/bin/env bash
    if [[ "{{path}}" == *.sql ]]; then
        echo "🔄 Transforming: {{path}}"
        python -m pg_idempotent transform -i "{{path}}" --dry-run
    else
        echo "📁 Changed: {{path}} (non-SQL file)"
    fi

# Watch specific file types
watch-sql path="examples":
    watchexec --exts sql --watch {{path}} -- just transform-watch '{}'

watch-code path="src":
    watchexec \
        --exts py,ts,js,jsx,tsx,go,rs,java,c,cpp,h,hpp \
        --watch {{path}} \
        --restart \
        --clear \
        -- just test

watch-config path=".":
    watchexec \
        --exts toml,yaml,yml,json,ini,cfg,conf,env \
        --watch {{path}} \
        --restart \
        -- echo "Config changed, reloading..."

# Watch everything with smart actions
watch-all:
    watchexec \
        --exts sql,py,ts,js,json,yaml,yml,toml,md,rst,txt,ini,cfg,conf,env,tsx,jsx,go,rs,java,c,cpp,h,hpp,sh,bash,zsh,fish \
        --watch src \
        --watch tests \
        --watch examples \
        --watch pyproject.toml \
        --watch Justfile \
        --restart \
        --clear \
        --on-busy-update do-nothing \
        -- just smart-reload

# Generate documentation
docs:
    pdoc --html --output-dir docs src/pg_idempotent

# Check if all dependencies are installed
check-deps:
    @echo "Checking dependencies..."
    @python -c "import typer" && echo "✅ typer" || echo "❌ typer"
    @python -c "import pglast" && echo "✅ pglast" || echo "❌ pglast"
    @python -c "import rich" && echo "✅ rich" || echo "❌ rich"
    @command -v watchexec &> /dev/null && echo "✅ watchexec" || echo "❌ watchexec (install: cargo install watchexec-cli)"

# Install watchexec if not present
install-watchexec:
    #!/usr/bin/env bash
    if ! command -v watchexec &> /dev/null; then
        echo "Installing watchexec..."
        if command -v cargo &> /dev/null; then
            cargo install watchexec-cli
        elif command -v brew &> /dev/null; then
            brew install watchexec
        else
            echo "Please install watchexec: https://github.com/watchexec/watchexec"
            exit 1
        fi
    else
        echo "✅ watchexec already installed"
    fi

# Smart reload based on file type
smart-reload:
    #!/usr/bin/env bash
    # Get the changed file from watchexec environment
    if [ -n "$WATCHEXEC_WRITTEN_PATH" ]; then
        file="$WATCHEXEC_WRITTEN_PATH"
        echo "🔄 Changed: $file"
        
        case "$file" in
            *.sql)
                echo "📄 SQL file changed, transforming..."
                just transform "$file"
                ;;
            *.py)
                echo "🐍 Python file changed, running tests..."
                just test
                ;;
            *.toml|*.yaml|*.yml|*.json)
                echo "⚙️  Config file changed, validating..."
                just lint
                ;;
            *)
                echo "📝 File changed: $file"
                ;;
        esac
    fi

# Run a specific example
example name:
    python -m pg_idempotent transform -i examples/{{name}}.sql -o examples/{{name}}_idempotent.sql -v

# Create a new example file
new-example name:
    @mkdir -p examples
    @echo "-- Example: {{name}}" > examples/{{name}}.sql
    @echo "CREATE TABLE {{name}}_table (id SERIAL PRIMARY KEY);" >> examples/{{name}}.sql
    @echo "✅ Created examples/{{name}}.sql"

# Show project info
info:
    @echo "PostgreSQL Idempotent Migration Tool"
    @echo "===================================="
    @echo "Version: $(python -c 'import tomli; print(tomli.load(open("pyproject.toml", "rb"))["project"]["version"])')"
    @echo "Python: $(python --version)"
    @echo "Location: $(pwd)"
    @echo ""
    @echo "Quick commands:"
    @echo "  just transform <file>    - Transform a SQL file"
    @echo "  just test               - Run tests"
    @echo "  just lint               - Format and lint code"
    @echo "  just watch              - Watch and auto-transform"

# Generate SQL test cases using Fireworks AI
generate-tests count="100" config="balanced":
    @echo "🤖 Generating {{count}} SQL test cases..."
    python scripts/generate_sql_tests.py --count {{count}} --config {{config}}

# Generate tests in parallel (fast mode)
generate-tests-fast count="100" config="balanced":
    @echo "⚡ Fast parallel generation of {{count}} test cases..."
    python scripts/generate_sql_tests_parallel.py --count {{count}} --config {{config}} --batch-size 5 --max-concurrent 10

# Benchmark to find optimal generation settings
benchmark-generation:
    @echo "📊 Running generation benchmark..."
    python scripts/benchmark_generator.py

# Set up Fireworks API key
setup-fireworks key:
    @echo "export FIREWORKS_API_KEY={{key}}" >> .env
    @echo "✅ Fireworks API key saved to .env"

# Check available Fireworks AI models
check-models:
    @echo "🔍 Checking available Fireworks AI models..."
    python scripts/check_fireworks_models.py