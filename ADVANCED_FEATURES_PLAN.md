# Advanced Features Plan for pg-idempotent

## Current Status ✅
- **Core transformation engine**: Working perfectly
- **SQL parsing**: Handles dollar quotes, comments, complex functions
- **Statement detection**: All DDL types supported (CREATE TABLE, TYPE, INDEX, FUNCTION, POLICY, etc.)
- **CLI interface**: Rich, functional interface with multiple commands
- **Test coverage**: 11/11 tests passing (100% core functionality)

## Phase 1: Dependency Analysis System

### 1.1 SQL Object Dependency Detection
**Goal**: Analyze SQL statements to identify dependencies between objects

**Implementation**:
```python
# New module: src/pg_idempotent/analyzer/dependency_analyzer.py
class DependencyAnalyzer:
    def extract_dependencies(self, statements: List[ParsedStatement]) -> DependencyGraph
    def find_table_references(self, statement: ParsedStatement) -> List[str]
    def find_type_references(self, statement: ParsedStatement) -> List[str]
    def find_function_references(self, statement: ParsedStatement) -> List[str]
```

**Dependencies to detect**:
- **Tables**: Foreign keys, inheritance, references in triggers/functions
- **Types**: Used in table columns, function parameters/returns
- **Functions**: Called by other functions, used in triggers/constraints
- **Indexes**: Depend on tables and can reference functions
- **Views**: Depend on tables/views, can use functions
- **Policies**: Depend on tables and functions
- **Triggers**: Depend on tables and functions

### 1.2 Dependency Graph Structure
```python
@dataclass
class SQLObject:
    name: str
    schema: str
    object_type: str  # 'table', 'type', 'function', etc.
    statement: ParsedStatement
    dependencies: Set[str]  # Objects this depends on
    dependents: Set[str]    # Objects that depend on this

class DependencyGraph:
    def add_object(self, obj: SQLObject)
    def get_dependencies(self, obj_name: str) -> Set[str]
    def get_dependents(self, obj_name: str) -> Set[str]
    def topological_sort(self) -> List[SQLObject]
    def detect_cycles(self) -> List[List[str]]
```

### 1.3 Advanced Parsing for Dependencies
- **AST analysis**: Deep parsing of CREATE statements to find references
- **Regex patterns**: Backup detection for complex cases
- **Schema-qualified names**: Handle `schema.object` references
- **Cross-schema dependencies**: Track dependencies across schemas

## Phase 2: Schema Splitting & Organization

### 2.1 Schema Categorization System
**Goal**: Automatically categorize SQL objects by type and purpose

**Categories**:
1. **Foundation** (`00_foundation/`): Types, enums, extensions
2. **Core Tables** (`01_tables/`): Main application tables
3. **Security** (`02_security/`): RLS policies, roles, permissions
4. **Functions** (`03_functions/`): Stored procedures, triggers
5. **Views** (`04_views/`): Views and materialized views
6. **Indexes** (`05_indexes/`): Performance indexes
7. **Constraints** (`06_constraints/`): Foreign keys, checks
8. **Data** (`07_data/`): Initial data, seeds

### 2.2 Supabase Integration
**Goal**: Support Supabase's declarative schema format

**File structure**:
```
supabase/
├── schemas/
│   ├── 00_foundation/
│   │   ├── types.sql
│   │   └── extensions.sql
│   ├── 01_tables/
│   │   ├── users.sql
│   │   ├── profiles.sql
│   │   └── posts.sql
│   ├── 02_security/
│   │   ├── rls_policies.sql
│   │   └── permissions.sql
│   └── ...
└── migrations/
    └── [timestamp]_split_schema.sql
```

### 2.3 Smart File Splitting
```python
# New module: src/pg_idempotent/splitter/schema_splitter.py
class SchemaSplitter:
    def split_by_dependencies(self, statements: List[ParsedStatement]) -> Dict[str, List[ParsedStatement]]
    def split_by_category(self, statements: List[ParsedStatement]) -> Dict[str, List[ParsedStatement]]
    def generate_file_structure(self, categorized: Dict[str, List[ParsedStatement]]) -> Dict[Path, str]
    def create_migration_file(self, original_file: Path, split_files: Dict[Path, str]) -> str
```

## Phase 3: Advanced CLI Features

### 3.1 New Commands
```bash
# Split a large SQL file into organized schemas
pg-idempotent split input.sql --output-dir schemas/ --format supabase

# Analyze dependencies and show dependency graph
pg-idempotent analyze input.sql --show-graph --detect-cycles

# Merge schema files back into a single migration
pg-idempotent merge schemas/ --output migration.sql --topological-order

# Validate schema dependencies
pg-idempotent validate schemas/ --check-dependencies --check-circular
```

### 3.2 Enhanced Analysis Features
```python
@app.command()
def split(
    input_file: Path,
    output_dir: Path = typer.Option("schemas", help="Output directory"),
    format: str = typer.Option("supabase", help="Output format (supabase, standard)"),
    dry_run: bool = typer.Option(False, help="Preview split without writing files"),
    show_dependencies: bool = typer.Option(False, help="Show dependency graph")
)

@app.command() 
def analyze(
    input_path: Path,
    show_graph: bool = typer.Option(False, help="Display dependency graph"),
    detect_cycles: bool = typer.Option(True, help="Check for circular dependencies"),
    output_format: str = typer.Option("table", help="Output format (table, json, graph)")
)
```

## Phase 4: Advanced Transformation Features

### 4.1 Intelligent Dependency Ordering
- **Topological sort**: Ensure dependencies are created before dependents
- **Cycle detection**: Identify and report circular dependencies
- **Smart batching**: Group independent objects for parallel execution

### 4.2 Cross-Schema Support
- **Schema-aware parsing**: Handle multiple schemas in one file
- **Qualified name resolution**: Resolve `schema.object` references
- **Schema migration ordering**: Order schema creation/modification

### 4.3 Advanced Idempotent Patterns
- **Conditional migrations**: Only run if certain conditions are met
- **Version-aware transforms**: Handle different PostgreSQL versions
- **Rollback generation**: Generate rollback scripts automatically

## Phase 5: Integration & Tooling

### 5.1 Database Integration
```python
# New module: src/pg_idempotent/database/inspector.py
class DatabaseInspector:
    def get_existing_objects(self, connection: Connection) -> Set[SQLObject]
    def compare_with_file(self, file_objects: Set[SQLObject]) -> DiffResult
    def generate_migration_plan(self, diff: DiffResult) -> List[str]
```

### 5.2 CI/CD Integration
- **GitHub Actions**: Automated schema validation
- **Pre-commit hooks**: Validate SQL before commits
- **Migration validation**: Ensure migrations are idempotent

### 5.3 Development Tools
- **VS Code extension**: Syntax highlighting for transformed SQL
- **Web interface**: Visual dependency graph explorer
- **Documentation generator**: Auto-generate schema docs

## Implementation Priority

### High Priority (Phase 1)
1. ✅ **Core parsing fixes** - COMPLETED
2. 🔄 **Dependency analysis system** - IN PROGRESS
3. **Basic schema splitting**
4. **Topological sorting**

### Medium Priority (Phase 2-3)
5. **Supabase integration**
6. **Advanced CLI commands**
7. **Cross-schema support**

### Low Priority (Phase 4-5)
8. **Database integration**
9. **CI/CD tooling**
10. **Web interface**

## Technical Architecture

### File Structure
```
src/pg_idempotent/
├── analyzer/
│   ├── __init__.py
│   ├── dependency_analyzer.py
│   ├── object_extractor.py
│   └── graph.py
├── splitter/
│   ├── __init__.py
│   ├── schema_splitter.py
│   ├── categorizer.py
│   └── file_generator.py
├── database/
│   ├── __init__.py
│   ├── inspector.py
│   └── migrator.py
└── formats/
    ├── __init__.py
    ├── supabase.py
    └── standard.py
```

### Key Design Principles
1. **Modular architecture**: Each feature in separate, testable modules
2. **Plugin system**: Support for different output formats (Supabase, etc.)
3. **Comprehensive testing**: Test coverage for all new features
4. **Backward compatibility**: Don't break existing functionality
5. **Performance**: Handle large SQL files efficiently
6. **Documentation**: Clear examples and usage guides

## Success Metrics
- Handle SQL files with 1000+ statements
- Detect 95%+ of dependency relationships correctly
- Generate valid Supabase schema structures
- Process large files in <10 seconds
- Zero breaking changes to existing API

---

*This plan provides a roadmap for transforming pg-idempotent from a basic idempotent transformer into a comprehensive SQL schema management and analysis tool.*