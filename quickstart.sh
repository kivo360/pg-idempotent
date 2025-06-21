#!/usr/bin/env bash
# PostgreSQL Idempotent Migration Tool - Quick Start Script
# This script sets up the project and runs the first transformation

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Banner
echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════╗"
echo "║   PostgreSQL Idempotent Migration Tool         ║"
echo "║            Quick Start Setup                   ║"
echo "╚════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is required but not found${NC}"
    echo "Please install Python 3.10 or later"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "${GREEN}✓ Python ${PYTHON_VERSION} detected${NC}"

# Check for package managers
if command -v uv &> /dev/null; then
    echo -e "${GREEN}✓ UV detected (fast mode enabled)${NC}"
    USE_UV=true
elif command -v pip &> /dev/null; then
    echo -e "${GREEN}✓ pip detected${NC}"
    USE_UV=false
else
    echo -e "${RED}❌ No Python package manager found${NC}"
    exit 1
fi

# Check for Just command runner
if ! command -v just &> /dev/null; then
    echo -e "${YELLOW}📦 Installing Just command runner...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install just || {
            echo -e "${YELLOW}Install Just manually: https://github.com/casey/just${NC}"
        }
    else
        echo -e "${YELLOW}Install Just for better experience: https://github.com/casey/just${NC}"
        echo -e "${YELLOW}Falling back to make...${NC}"
    fi
fi

# Create project structure
echo -e "${YELLOW}📁 Creating project structure...${NC}"
mkdir -p src/pg_idempotent/{parser,transformer,cli,utils}
mkdir -p tests/{unit,integration,fixtures}
mkdir -p examples
mkdir -p .shrimpy

# Create example SQL
echo -e "${YELLOW}📝 Creating example SQL files...${NC}"
cat > examples/simple.sql << 'EOF'
-- Simple example migration
CREATE TYPE user_status AS ENUM ('active', 'inactive', 'pending');

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    status user_status DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);
EOF

# Create Shrimpy tasks
echo -e "${YELLOW}🦐 Setting up Shrimpy tasks...${NC}"
cp .shrimpy/tasks.json.template .shrimpy/tasks.json 2>/dev/null || cat > .shrimpy/tasks.json << 'EOF'
{
  "version": "1.0.0",
  "project": "PostgreSQL Idempotent Migration Tool",
  "tasks": [
    {
      "id": "39a6fe92-0833-471e-9c19-9138166b718f",
      "name": "Create PostgreSQL AST parser integration",
      "status": "pending",
      "description": "Integrate pglast parser with error handling"
    },
    {
      "id": "ec928917-b3ba-41c6-8805-4f7820db92ce",
      "name": "Implement dollar-quote preprocessor",
      "status": "pending",
      "description": "Handle PostgreSQL dollar-quoted strings"
    }
  ]
}
EOF

# Install dependencies
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
if [ "$USE_UV" = true ]; then
    uv sync --all-extras
    source .venv/bin/activate
else
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -e ".[dev]"
fi

# Install pre-commit hooks
if command -v pre-commit &> /dev/null; then
    pre-commit install --install-hooks
    echo -e "${GREEN}✓ Pre-commit hooks installed${NC}"
fi

# Run initial test
echo -e "${YELLOW}🧪 Running initial test...${NC}"
python -m pg_idempotent transform -i examples/simple.sql --dry-run

# Success message
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        ✅ Setup Complete! 🎉                   ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Quick commands:${NC}"
echo ""
if command -v just &> /dev/null; then
    echo "  just transform examples/simple.sql    # Transform a file"
    echo "  just test                            # Run tests"
    echo "  just watch                           # Auto-transform on changes"
else
    echo "  python -m pg_idempotent transform -i <file>  # Transform a file"
    echo "  pytest                                       # Run tests"
fi
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Implement parser integration in src/pg_idempotent/parser/"
echo "  2. Build transformation templates in src/pg_idempotent/transformer/"
echo "  3. Run 'just shrimpy-list' to see all tasks"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"