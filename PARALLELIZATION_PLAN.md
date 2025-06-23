# Parallelization Plan for pg-idempotent Advanced Features

## Overview
Split development into 4 parallel tracks with well-defined interfaces, enabling simultaneous development by multiple developers.

## Architecture: Plugin-Based System

### Core Interface Definitions
```python
# src/pg_idempotent/interfaces/
from abc import ABC, abstractmethod
from typing import List, Dict, Set, Any
from dataclasses import dataclass

@dataclass
class SQLObject:
    name: str
    schema: str
    object_type: str  # 'table', 'type', 'function', etc.
    raw_sql: str
    dependencies: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DependencyGraph:
    objects: Dict[str, SQLObject]
    edges: Dict[str, Set[str]]  # object_name -> dependencies
    
class DependencyAnalyzer(ABC):
    @abstractmethod
    def analyze(self, statements: List[ParsedStatement]) -> DependencyGraph:
        pass

class SchemaSplitter(ABC):
    @abstractmethod
    def split(self, graph: DependencyGraph, strategy: str) -> Dict[str, List[SQLObject]]:
        pass

class FormatHandler(ABC):
    @abstractmethod
    def generate_files(self, categorized: Dict[str, List[SQLObject]]) -> Dict[str, str]:
        pass
```

## Parallel Track 1: rustworkx Dependency Engine 🦀
**Owner**: Developer A  
**Timeline**: 2-3 weeks  
**Priority**: Critical Path

### Deliverables
```python
# src/pg_idempotent/analyzer/rustworkx_analyzer.py
import rustworkx as rx
from typing import List, Dict, Set, Optional
import re

class RustworkxDependencyAnalyzer(DependencyAnalyzer):
    def __init__(self):
        self.graph = rx.PyDiGraph()
        self.node_map: Dict[str, int] = {}  # object_name -> node_index
        self.reverse_map: Dict[int, str] = {}  # node_index -> object_name
    
    def analyze(self, statements: List[ParsedStatement]) -> DependencyGraph:
        """Build dependency graph using rustworkx"""
        self._build_graph(statements)
        return self._extract_dependencies()
    
    def _build_graph(self, statements: List[ParsedStatement]):
        """Build rustworkx graph from SQL statements"""
        # Add all objects as nodes first
        for stmt in statements:
            if stmt.object_name:
                obj_id = f"{stmt.schema_name or 'public'}.{stmt.object_name}"
                if obj_id not in self.node_map:
                    node_idx = self.graph.add_node(stmt)
                    self.node_map[obj_id] = node_idx
                    self.reverse_map[node_idx] = obj_id
        
        # Add dependency edges
        for stmt in statements:
            if stmt.object_name:
                source_id = f"{stmt.schema_name or 'public'}.{stmt.object_name}"
                dependencies = self._extract_dependencies_from_statement(stmt)
                
                for dep in dependencies:
                    if dep in self.node_map:
                        # Add edge: source depends on dep
                        self.graph.add_edge(
                            self.node_map[dep], 
                            self.node_map[source_id], 
                            "depends_on"
                        )
    
    def _extract_dependencies_from_statement(self, stmt: ParsedStatement) -> Set[str]:
        """Extract dependencies from a single statement"""
        dependencies = set()
        
        # Foreign key references
        fk_pattern = r'REFERENCES\s+(?:(\w+)\.)?(\w+)\s*\('
        for match in re.finditer(fk_pattern, stmt.raw_sql, re.IGNORECASE):
            schema = match.group(1) or 'public'
            table = match.group(2)
            dependencies.add(f"{schema}.{table}")
        
        # Type references in columns
        type_pattern = r'\b(?:(\w+)\.)?(\w+)\s+(?:NOT\s+NULL|DEFAULT|PRIMARY|UNIQUE|CHECK)'
        # ... more extraction logic
        
        return dependencies
    
    def topological_sort(self) -> List[str]:
        """Get topological ordering using rustworkx"""
        try:
            sorted_indices = rx.topological_sort(self.graph)
            return [self.reverse_map[idx] for idx in sorted_indices]
        except rx.DAGHasCycle:
            # Handle circular dependencies
            return self._handle_cycles()
    
    def detect_cycles(self) -> List[List[str]]:
        """Find strongly connected components (cycles)"""
        sccs = rx.strongly_connected_components(self.graph)
        cycles = []
        for scc in sccs:
            if len(scc) > 1:  # Cycle detected
                cycle = [self.reverse_map[idx] for idx in scc]
                cycles.append(cycle)
        return cycles
    
    def shortest_path(self, source: str, target: str) -> Optional[List[str]]:
        """Find shortest dependency path between objects"""
        if source not in self.node_map or target not in self.node_map:
            return None
        
        path = rx.dijkstra_shortest_paths(
            self.graph, 
            self.node_map[source], 
            target=self.node_map[target]
        )
        
        if self.node_map[target] in path:
            indices = path[self.node_map[target]]
            return [self.reverse_map[idx] for idx in indices]
        return None
```

### Why rustworkx?
- **Performance**: Rust-powered graph algorithms, 10-100x faster than NetworkX
- **Parallel processing**: Built-in parallel graph operations
- **Rich algorithms**: Topological sort, cycle detection, shortest paths, centrality
- **Memory efficiency**: Optimized for large graphs (10k+ nodes)
- **Python native**: No FFI overhead, direct Python integration

### Advanced Graph Algorithms
```python
class AdvancedGraphAnalyzer:
    def __init__(self, graph: rx.PyDiGraph):
        self.graph = graph
    
    def find_critical_objects(self) -> List[str]:
        """Objects that many others depend on"""
        centrality = rx.betweenness_centrality(self.graph)
        return sorted(centrality.items(), key=lambda x: x[1], reverse=True)
    
    def find_leaf_objects(self) -> List[str]:
        """Objects with no dependencies (safe to drop)"""
        return [node for node in self.graph.node_indices() 
                if self.graph.in_degree(node) == 0]
    
    def find_dependency_clusters(self) -> List[List[str]]:
        """Groups of tightly coupled objects"""
        components = rx.weakly_connected_components(self.graph)
        return [[self.reverse_map[idx] for idx in component] 
                for component in components]
    
    def calculate_migration_levels(self) -> Dict[str, int]:
        """Assign objects to migration levels based on dependencies"""
        levels = {}
        sorted_nodes = rx.topological_sort(self.graph)
        
        for node_idx in sorted_nodes:
            obj_name = self.reverse_map[node_idx]
            # Level = max(dependency_levels) + 1
            deps = self.graph.predecessors(node_idx)
            if not deps:
                levels[obj_name] = 0
            else:
                max_dep_level = max(levels[self.reverse_map[dep]] for dep in deps)
                levels[obj_name] = max_dep_level + 1
        
        return levels
```

### Integration Points
```python
# Plugin registration
class RustworkxDependencyPlugin(DependencyAnalyzer):
    def __init__(self):
        self.analyzer = RustworkxDependencyAnalyzer()
    
    def analyze(self, statements: List[ParsedStatement]) -> DependencyGraph:
        return self.analyzer.analyze(statements)
    
    def get_execution_order(self, statements: List[ParsedStatement]) -> List[str]:
        self.analyzer.analyze(statements)
        return self.analyzer.topological_sort()
```

### Test Interface
```python
# tests/test_rustworkx_analyzer.py
def test_rustworkx_dependency_analysis():
    analyzer = RustworkxDependencyAnalyzer()
    statements = [
        create_parsed_statement("CREATE TABLE users (id INT);", "users"),
        create_parsed_statement("CREATE TABLE posts (id INT, user_id INT REFERENCES users(id));", "posts")
    ]
    
    graph = analyzer.analyze(statements)
    assert "users" in analyzer.node_map
    assert "posts" in analyzer.node_map
    
    order = analyzer.topological_sort()
    assert order.index("users") < order.index("posts")

def test_cycle_detection():
    # Create circular dependency scenario
    analyzer = RustworkxDependencyAnalyzer()
    # ... setup circular deps
    cycles = analyzer.detect_cycles()
    assert len(cycles) > 0
```

## Parallel Track 2: Schema Splitting Engine 🔀
**Owner**: Developer B  
**Timeline**: 2-3 weeks  
**Priority**: Critical Path

### Deliverables
```python
# src/pg_idempotent/splitter/
class SchemaSplitterEngine:
    def __init__(self, strategy: str = "dependency_based"):
        self.strategy = strategy
        self.categorizers = self._load_categorizers()
    
    def split_by_dependencies(self, graph: DependencyGraph) -> Dict[str, List[SQLObject]]:
        """Split based on topological sort levels"""
        
    def split_by_category(self, graph: DependencyGraph) -> Dict[str, List[SQLObject]]:
        """Split by object types and purposes"""
        
    def split_hybrid(self, graph: DependencyGraph) -> Dict[str, List[SQLObject]]:
        """Combine dependency and category-based splitting"""

class SupabaseSplitter(SchemaSplitter):
    """Supabase-specific splitting logic"""
    
class StandardSplitter(SchemaSplitter):
    """Generic SQL splitting logic"""
```

### Categorization System
```python
@dataclass
class Category:
    name: str
    priority: int  # Execution order
    patterns: List[str]  # SQL patterns to match
    dependencies: List[str]  # Required categories

SUPABASE_CATEGORIES = [
    Category("00_extensions", 0, ["CREATE EXTENSION"], []),
    Category("01_types", 1, ["CREATE TYPE", "CREATE DOMAIN"], ["00_extensions"]),
    Category("02_tables", 2, ["CREATE TABLE"], ["01_types"]),
    Category("03_security", 3, ["CREATE POLICY", "GRANT", "REVOKE"], ["02_tables"]),
    Category("04_functions", 4, ["CREATE FUNCTION", "CREATE PROCEDURE"], ["02_tables"]),
    Category("05_triggers", 5, ["CREATE TRIGGER"], ["02_tables", "04_functions"]),
    Category("06_views", 6, ["CREATE VIEW"], ["02_tables", "04_functions"]),
    Category("07_indexes", 7, ["CREATE INDEX"], ["02_tables"]),
    Category("08_data", 8, ["INSERT", "COPY"], ["02_tables"]),
]
```

### Test Interface
```python
def test_schema_splitting():
    graph = create_test_dependency_graph()
    splitter = SupabaseSplitter()
    result = splitter.split(graph, "hybrid")
    
    assert "00_extensions" in result
    assert "02_tables" in result
    assert len(result["02_tables"]) > 0
```

## Parallel Track 3: Migra Integration & Validation 🔄
**Owner**: Developer C  
**Timeline**: 1-2 weeks  
**Priority**: High

### Migra Integration
```python
# src/pg_idempotent/validation/migra_validator.py
from migra import Migration
import sqlalchemy

class MigraValidator:
    def __init__(self, db_url: str):
        self.engine = sqlalchemy.create_engine(db_url)
    
    def validate_migration(self, original_sql: str, transformed_sql: str) -> ValidationResult:
        """Ensure transformed SQL produces same database state"""
        
    def generate_diff(self, source_sql: str, target_sql: str) -> str:
        """Use migra to show differences"""
        
    def validate_idempotency(self, sql: str) -> bool:
        """Verify SQL can be run multiple times safely"""

@dataclass
class ValidationResult:
    is_valid: bool
    differences: List[str]
    warnings: List[str]
    migra_output: str
```

### Database Comparison Engine
```python
class DatabaseComparator:
    def compare_schemas(self, schema1: str, schema2: str) -> ComparisonResult:
        """Deep comparison of database schemas"""
        
    def validate_dependencies(self, objects: List[SQLObject]) -> List[ValidationError]:
        """Ensure all dependencies exist and are valid"""
        
    def check_circular_dependencies(self, graph: DependencyGraph) -> List[List[str]]:
        """Find circular dependency chains"""
```

### Test Interface
```python
def test_migra_validation():
    validator = MigraValidator("postgresql://test")
    original = "CREATE TABLE users (id INT);"
    transformed = "DO $$ BEGIN IF NOT EXISTS (...) THEN CREATE TABLE users (id INT); END IF; END $$;"
    
    result = validator.validate_migration(original, transformed)
    assert result.is_valid
    assert len(result.differences) == 0
```

## Parallel Track 4: LLM Schema Naming & Advanced CLI 🤖
**Owner**: Developer D  
**Timeline**: 2-3 weeks  
**Priority**: Medium

### LLM Schema Naming System
```python
# src/pg_idempotent/naming/llm_namer.py
import os
import openai
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class NamingContext:
    sql_objects: List[SQLObject]
    object_types: Set[str]
    domain_hints: Optional[str] = None  # e.g., "e-commerce", "healthcare"
    existing_names: Set[str] = field(default_factory=set)

class LLMSchemaNamer:
    def __init__(self, 
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 model: str = "gpt-4"):
        # Flexible API configuration
        self.api_key = api_key or os.getenv('PG_IDEMPOTENT_API_KEY') or os.getenv('OPENAI_API_KEY')
        self.base_url = base_url or os.getenv('PG_IDEMPOTENT_BASE_URL') or "https://api.openai.com/v1"
        self.model = model
        
        if not self.api_key:
            raise ValueError("API key required. Set PG_IDEMPOTENT_API_KEY or OPENAI_API_KEY environment variable")
        
        # Configure OpenAI client
        openai.api_key = self.api_key
        openai.api_base = self.base_url
    
    def generate_schema_names(self, context: NamingContext) -> Dict[str, str]:
        """Generate semantic schema names for object groups"""
        prompt = self._build_naming_prompt(context)
        
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temperature for more consistent naming
            max_tokens=1000
        )
        
        return self._parse_naming_response(response.choices[0].message.content)
    
    def _build_naming_prompt(self, context: NamingContext) -> str:
        """Build context-aware prompt for schema naming"""
        object_summary = self._summarize_objects(context.sql_objects)
        
        prompt = f"""
I have a PostgreSQL database with the following objects that need to be organized into semantic schemas:

Object Summary:
{object_summary}

Object Types Present: {', '.join(context.object_types)}

{f"Domain Context: {context.domain_hints}" if context.domain_hints else ""}

Please suggest semantic schema names for organizing these objects. Consider:
1. Logical grouping by business function
2. Dependency relationships (foundational objects first)
3. Clear, descriptive names (snake_case)
4. Avoid conflicts with existing names: {', '.join(context.existing_names)}

Provide schema names with brief descriptions of what belongs in each.
"""
        return prompt
    
    def _get_system_prompt(self) -> str:
        return """You are a database architect specializing in PostgreSQL schema organization.
Your task is to suggest logical, semantic schema names for grouping database objects.

Guidelines:
- Use clear, descriptive names in snake_case
- Consider business domains and logical groupings
- Respect dependency order (types before tables, tables before views, etc.)
- Suggest 3-8 schemas typically
- Include brief descriptions

Response format:
schema_name: Brief description of what this schema contains
"""
    
    def _summarize_objects(self, objects: List[SQLObject]) -> str:
        """Create a concise summary of database objects"""
        summary = []
        by_type = {}
        
        for obj in objects:
            if obj.object_type not in by_type:
                by_type[obj.object_type] = []
            by_type[obj.object_type].append(obj.name)
        
        for obj_type, names in by_type.items():
            if len(names) <= 5:
                summary.append(f"{obj_type.upper()}: {', '.join(names)}")
            else:
                sample = names[:3]
                summary.append(f"{obj_type.upper()}: {', '.join(sample)} (and {len(names)-3} more)")
        
        return '\n'.join(summary)
    
    def _parse_naming_response(self, response: str) -> Dict[str, str]:
        """Parse LLM response into schema name mappings"""
        schemas = {}
        for line in response.strip().split('\n'):
            if ':' in line:
                name, description = line.split(':', 1)
                schemas[name.strip()] = description.strip()
        return schemas

class SmartSchemaNamer:
    """Combines rule-based and LLM naming strategies"""
    
    def __init__(self, use_llm: bool = True, fallback_to_rules: bool = True):
        self.use_llm = use_llm
        self.fallback_to_rules = fallback_to_rules
        self.llm_namer = LLMSchemaNamer() if use_llm else None
        self.rule_namer = RuleBasedNamer()
    
    def name_schemas(self, 
                    object_groups: Dict[str, List[SQLObject]], 
                    domain_hints: Optional[str] = None) -> Dict[str, str]:
        """Generate schema names using LLM with rule-based fallback"""
        
        if self.use_llm and self.llm_namer:
            try:
                # Prepare context for LLM
                all_objects = [obj for group in object_groups.values() for obj in group]
                context = NamingContext(
                    sql_objects=all_objects,
                    object_types={obj.object_type for obj in all_objects},
                    domain_hints=domain_hints
                )
                
                # Get LLM suggestions
                llm_names = self.llm_namer.generate_schema_names(context)
                
                # Map object groups to LLM-suggested names
                return self._map_groups_to_names(object_groups, llm_names)
                
            except Exception as e:
                print(f"LLM naming failed: {e}")
                if not self.fallback_to_rules:
                    raise
        
        # Fallback to rule-based naming
        return self.rule_namer.name_schemas(object_groups)

class RuleBasedNamer:
    """Fallback rule-based schema naming"""
    
    CATEGORY_NAMES = {
        'types': 'foundation_types',
        'extensions': 'extensions', 
        'tables': 'core_tables',
        'functions': 'business_logic',
        'views': 'data_views',
        'policies': 'security_policies',
        'indexes': 'performance_indexes',
        'triggers': 'event_handlers'
    }
    
    def name_schemas(self, object_groups: Dict[str, List[SQLObject]]) -> Dict[str, str]:
        """Generate schema names using predefined rules"""
        schema_names = {}
        
        for group_key, objects in object_groups.items():
            # Determine primary object type in group
            type_counts = {}
            for obj in objects:
                type_counts[obj.object_type] = type_counts.get(obj.object_type, 0) + 1
            
            primary_type = max(type_counts.items(), key=lambda x: x[1])[0]
            schema_names[group_key] = self.CATEGORY_NAMES.get(primary_type, f"custom_{primary_type}")
        
        return schema_names
```

### Environment Configuration
```python
# src/pg_idempotent/config/api_config.py
import os
from typing import Optional
from dataclasses import dataclass

@dataclass
class APIConfig:
    api_key: str
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4"
    timeout: int = 30
    max_retries: int = 3

def load_api_config() -> Optional[APIConfig]:
    """Load API configuration from environment variables"""
    
    # Priority order for API keys:
    # 1. PG_IDEMPOTENT_API_KEY (our specific key)
    # 2. OPENAI_API_KEY (standard OpenAI key)
    api_key = os.getenv('PG_IDEMPOTENT_API_KEY') or os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        return None
    
    return APIConfig(
        api_key=api_key,
        base_url=os.getenv('PG_IDEMPOTENT_BASE_URL', "https://api.openai.com/v1"),
        model=os.getenv('PG_IDEMPOTENT_MODEL', "gpt-4"),
        timeout=int(os.getenv('PG_IDEMPOTENT_TIMEOUT', "30")),
        max_retries=int(os.getenv('PG_IDEMPOTENT_RETRIES', "3"))
    )

# Support for different providers
PROVIDER_CONFIGS = {
    'openai': {
        'base_url': 'https://api.openai.com/v1',
        'models': ['gpt-4', 'gpt-3.5-turbo']
    },
    'anthropic': {
        'base_url': 'https://api.anthropic.com/v1',
        'models': ['claude-3-opus', 'claude-3-sonnet']
    },
    'local': {
        'base_url': 'http://localhost:1234/v1',  # Common local LLM port
        'models': ['local-model']
    }
}
```

### Plugin System Architecture
```python
# src/pg_idempotent/plugins/
class PluginManager:
    def __init__(self):
        self.analyzers: Dict[str, DependencyAnalyzer] = {}
        self.splitters: Dict[str, SchemaSplitter] = {}
        self.formatters: Dict[str, FormatHandler] = {}
        self.namers: Dict[str, SchemaNamer] = {}  # New: Schema namers
    
    def register_namer(self, name: str, namer: SchemaNamer):
        self.namers[name] = namer
    
    def get_namer(self, name: str) -> SchemaNamer:
        return self.namers.get(name, self.namers.get('rule_based'))

# Auto-discovery of plugins
def discover_plugins():
    """Automatically load plugins from entry points"""
    import pkg_resources
    for entry_point in pkg_resources.iter_entry_points('pg_idempotent.plugins'):
        plugin = entry_point.load()
        plugin.register()
```

### Advanced CLI Commands
```python
@app.command()
def split(
    input_file: Path,
    output_dir: Path = typer.Option("schemas", help="Output directory"),
    format: str = typer.Option("supabase", help="Format: supabase, standard"),
    strategy: str = typer.Option("hybrid", help="Strategy: dependency, category, hybrid"),
    analyzer: str = typer.Option("rustworkx", help="Analyzer: rustworkx, python"),
    namer: str = typer.Option("llm", help="Naming strategy: llm, rule_based, hybrid"),
    domain: Optional[str] = typer.Option(None, help="Domain context for LLM naming (e.g., 'e-commerce', 'healthcare')"),
    dry_run: bool = typer.Option(False, help="Preview only"),
    validate: bool = typer.Option(True, help="Validate with migra"),
    parallel: bool = typer.Option(True, help="Parallel processing"),
    # LLM Configuration
    api_key: Optional[str] = typer.Option(None, help="Override API key"),
    model: str = typer.Option("gpt-4", help="LLM model to use"),
    no_llm: bool = typer.Option(False, help="Disable LLM naming, use rules only")
):
    """Split large SQL files into organized schemas with intelligent naming"""
    
    # Configure LLM naming
    if no_llm:
        namer = "rule_based"
    
    # Set API key if provided
    if api_key:
        os.environ['PG_IDEMPOTENT_API_KEY'] = api_key

@app.command()
def analyze(
    input_path: Path,
    analyzer: str = typer.Option("rust", help="Analyzer engine to use"),
    show_graph: bool = typer.Option(False, help="Display dependency graph"),
    detect_cycles: bool = typer.Option(True, help="Check for circular dependencies"),
    export_format: str = typer.Option("json", help="Export format: json, dot, mermaid"),
    output_file: Optional[Path] = typer.Option(None, help="Export graph to file")
):
    """Analyze SQL dependencies and structure"""

@app.command()
def merge(
    schema_dir: Path,
    output_file: Path,
    order: str = typer.Option("topological", help="Order: topological, category"),
    validate: bool = typer.Option(True, help="Validate result with migra")
):
    """Merge schema files back into single migration"""

@app.command()
def validate(
    input_path: Path,
    database_url: Optional[str] = typer.Option(None, help="Compare against database"),
    check_idempotency: bool = typer.Option(True, help="Verify idempotency"),
    check_dependencies: bool = typer.Option(True, help="Validate dependencies")
):
    """Validate SQL files and transformations"""
```

## Integration Timeline & Milestones

### Week 1-2: Foundation
- **Track 1**: Rust WorkX basic dependency extraction
- **Track 2**: Core splitting algorithms
- **Track 3**: Migra integration setup
- **Track 4**: Plugin system architecture

### Week 3-4: Core Features
- **Track 1**: Advanced AST parsing, topological sort
- **Track 2**: Supabase format support
- **Track 3**: Validation engine
- **Track 4**: Advanced CLI commands

### Week 5: Integration & Testing
- **All Tracks**: Integration testing
- **All Tracks**: Performance optimization
- **All Tracks**: Documentation

## Interface Contracts

### Data Flow
```
Raw SQL → ParsedStatements → DependencyGraph → CategorizedObjects → OutputFiles
     ↓                           ↓                     ↓              ↓
  [Parser]              [Rust Analyzer]        [Splitter]      [Formatter]
                             ↓                     ↓              ↓
                      [Migra Validator] ← [CLI Controller] → [Plugin Manager]
```

### Test Interfaces
Each track must provide:
1. **Unit tests** for their components
2. **Integration tests** with mock interfaces
3. **Performance benchmarks** for their algorithms
4. **API documentation** with examples

### Mock Implementations
```python
# For parallel development
class MockRustAnalyzer(DependencyAnalyzer):
    def analyze(self, statements): 
        return MockDependencyGraph()

class MockSupabaseSplitter(SchemaSplitter):
    def split(self, graph, strategy):
        return {"00_types": [], "01_tables": []}
```

## Benefits of This Approach

1. **Parallel Development**: 4 developers can work simultaneously
2. **Clear Ownership**: Each track has defined responsibilities
3. **Testable Interfaces**: Easy to mock and test independently
4. **Plugin Architecture**: Easy to extend and maintain
5. **Performance**: Rust for heavy computation, Python for flexibility
6. **Validation**: Migra ensures correctness
7. **Flexibility**: Multiple analyzers/splitters/formatters

### Environment Variables & Configuration

```bash
# .env file example
PG_IDEMPOTENT_API_KEY=sk-proj-your-key-here
PG_IDEMPOTENT_BASE_URL=https://api.openai.com/v1
PG_IDEMPOTENT_MODEL=gpt-4
PG_IDEMPOTENT_TIMEOUT=30
PG_IDEMPOTENT_RETRIES=3

# Alternative providers
# PG_IDEMPOTENT_BASE_URL=https://api.anthropic.com/v1
# PG_IDEMPOTENT_MODEL=claude-3-sonnet-20240229
# PG_IDEMPOTENT_BASE_URL=http://localhost:1234/v1  # Local LLM
```

### CLI Usage Examples

```bash
# Basic split with LLM naming
pg-idempotent split massive_migration.sql --domain "e-commerce platform"

# Split with custom output directory and specific model
pg-idempotent split migration.sql --output-dir my_schemas/ --model gpt-3.5-turbo

# Split without LLM, using rule-based naming only  
pg-idempotent split migration.sql --no-llm

# Preview what the LLM would suggest
pg-idempotent split migration.sql --dry-run --domain "healthcare system"

# Use local LLM with custom API endpoint
PG_IDEMPOTENT_BASE_URL=http://localhost:1234/v1 pg-idempotent split migration.sql

# Split with specific analyzer and naming strategy
pg-idempotent split migration.sql --analyzer rustworkx --namer hybrid --format supabase
```

### Integration with Schema Splitting
```python
# Example workflow integration
def intelligent_schema_split(sql_file: Path, domain_hint: str = None):
    # 1. Parse and analyze with rustworkx
    analyzer = RustworkxDependencyAnalyzer()
    graph = analyzer.analyze(parse_sql_file(sql_file))
    
    # 2. Split into logical groups
    splitter = SupabaseSplitter()
    object_groups = splitter.split(graph, strategy="hybrid")
    
    # 3. Generate semantic names with LLM
    namer = SmartSchemaNamer(use_llm=True)
    schema_names = namer.name_schemas(object_groups, domain_hint)
    
    # 4. Generate organized file structure
    formatter = SupabaseFormatter()
    files = formatter.generate_files(object_groups, schema_names)
    
    return files
```

## rustworkx Integration Benefits

- **Performance**: Rust-powered graph algorithms, 10-100x faster than NetworkX
- **Rich algorithms**: Topological sort, cycle detection, shortest paths, centrality
- **Memory efficiency**: Optimized for large graphs (10k+ nodes)
- **Python native**: Direct integration, no compilation needed
- **Battle-tested**: Used by IBM Qiskit and other major projects

## LLM Naming Benefits

- **Semantic understanding**: Groups objects by business logic, not just technical type
- **Domain-aware**: Considers application context (e-commerce, healthcare, etc.)
- **Flexible**: Works with any OpenAI-compatible API (OpenAI, Anthropic, local LLMs)
- **Fallback**: Graceful degradation to rule-based naming if LLM fails
- **Consistent**: Lower temperature settings ensure stable, professional naming

This plan enables rapid, parallel development while maintaining quality and extensibility!