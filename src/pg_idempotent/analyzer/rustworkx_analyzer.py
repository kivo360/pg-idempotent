"""
Dependency graph analysis using rustworkx.

This module provides SQL object dependency analysis using graph algorithms
to detect circular dependencies and analyze object relationships.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
import logging

try:
    import rustworkx as rx
except ImportError:
    # Create a mock rx module to avoid AttributeError
    class MockRx:
        class PyDiGraph:
            pass
    rx = MockRx()
    logging.warning("rustworkx not installed. Graph analysis features will be limited.")

logger = logging.getLogger(__name__)


@dataclass
class SQLObject:
    """Represents a SQL database object with its dependencies."""
    
    name: str
    schema: Optional[str]
    object_type: str
    raw_sql: str
    dependencies: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and normalize object data."""
        if not self.name:
            raise ValueError("SQL object must have a name")
        
        # Normalize object type
        self.object_type = self.object_type.upper()
        
        # Ensure dependencies is a set
        if not isinstance(self.dependencies, set):
            self.dependencies = set(self.dependencies)
    
    @property
    def qualified_name(self) -> str:
        """Get fully qualified object name."""
        if self.schema:
            return f"{self.schema}.{self.name}"
        return self.name
    
    def __hash__(self):
        """Make object hashable for graph operations."""
        return hash((self.qualified_name, self.object_type))
    
    def __eq__(self, other):
        """Equality comparison."""
        if not isinstance(other, SQLObject):
            return False
        return (self.qualified_name == other.qualified_name and 
                self.object_type == other.object_type)


class DependencyExtractor:
    """Extract dependencies from SQL statements."""
    
    # Patterns for dependency extraction
    DEPENDENCY_PATTERNS = {
        # Table references
        r'FROM\s+(?:ONLY\s+)?([a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)?)': 'table',
        r'JOIN\s+([a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)?)': 'table',
        r'UPDATE\s+(?:ONLY\s+)?([a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)?)': 'table',
        r'INSERT\s+INTO\s+([a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)?)': 'table',
        r'DELETE\s+FROM\s+([a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)?)': 'table',
        r'REFERENCES\s+([a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)?)': 'table',
        r'INHERITS\s*\(\s*([a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)?)\s*\)': 'table',
        
        # Function calls
        r'([a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)?)\s*\(': 'function',
        
        # Type references
        r'::\s*([a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)?)': 'type',
        r'RETURNS\s+(?:SETOF\s+)?([a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)?)': 'type',
        
        # View references
        r'FROM\s+([a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)?)\s+': 'view',
    }
    
    # Object types that create dependencies
    CREATING_TYPES = {
        'CREATE_TABLE', 'CREATE_VIEW', 'CREATE_FUNCTION', 
        'CREATE_TRIGGER', 'CREATE_INDEX', 'CREATE_TYPE'
    }
    
    def __init__(self):
        self.compiled_patterns = {
            pattern: re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            for pattern in self.DEPENDENCY_PATTERNS
        }
    
    def extract_dependencies(self, sql_object: SQLObject) -> Set[str]:
        """Extract dependencies from SQL object."""
        dependencies = set()
        sql = sql_object.raw_sql
        
        # Skip if object doesn't create dependencies
        if sql_object.object_type not in self.CREATING_TYPES:
            return dependencies
        
        # Remove comments and string literals for cleaner parsing
        cleaned_sql = self._clean_sql(sql)
        
        # Extract dependencies using patterns
        for pattern, dep_type in self.DEPENDENCY_PATTERNS.items():
            for match in self.compiled_patterns[pattern].finditer(cleaned_sql):
                dep_name = match.group(1)
                
                # Skip self-references
                if dep_name.lower() != sql_object.name.lower():
                    dependencies.add(dep_name.lower())
        
        # Remove common false positives
        dependencies = self._filter_dependencies(dependencies, sql_object)
        
        return dependencies
    
    def _clean_sql(self, sql: str) -> str:
        """Remove comments and string literals from SQL."""
        # Remove single-line comments
        sql = re.sub(r'--[^\n]*', '', sql)
        
        # Remove multi-line comments
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        
        # Remove string literals (simple approach)
        sql = re.sub(r"'[^']*'", "''", sql)
        
        return sql
    
    def _filter_dependencies(self, dependencies: Set[str], sql_object: SQLObject) -> Set[str]:
        """Filter out false positive dependencies."""
        # Common PostgreSQL built-in functions/types to exclude
        BUILTINS = {
            'text', 'integer', 'bigint', 'boolean', 'timestamp', 'date', 'time',
            'varchar', 'char', 'numeric', 'decimal', 'real', 'double', 'precision',
            'serial', 'bigserial', 'uuid', 'json', 'jsonb', 'array', 'void',
            'now', 'current_timestamp', 'current_date', 'count', 'sum', 'avg',
            'min', 'max', 'coalesce', 'nullif', 'lower', 'upper', 'trim'
        }
        
        filtered = set()
        for dep in dependencies:
            # Split schema.object notation
            parts = dep.split('.')
            obj_name = parts[-1]
            
            # Skip built-ins
            if obj_name.lower() in BUILTINS:
                continue
                
            # Skip pg_ system schemas
            if len(parts) > 1 and parts[0].startswith('pg_'):
                continue
            
            filtered.add(dep)
        
        return filtered


class DependencyGraphAnalyzer:
    """Analyze SQL object dependencies using graph algorithms."""
    
    def __init__(self):
        self.extractor = DependencyExtractor()
        self.graph = None
        self.node_map = {}  # Map object names to node indices
        self.reverse_map = {}  # Map node indices to objects
        
        if rx is None:
            raise ImportError(
                "rustworkx is required for dependency analysis. "
                "Install with: pip install rustworkx"
            )
    
    def build_dependency_graph(self, sql_objects: List[SQLObject]) -> rx.PyDiGraph:
        """Build a directed graph of object dependencies."""
        self.graph = rx.PyDiGraph()
        self.node_map = {}
        self.reverse_map = {}
        
        # Add nodes for all objects
        for obj in sql_objects:
            node_idx = self.graph.add_node(obj)
            self.node_map[obj.qualified_name.lower()] = node_idx
            self.reverse_map[node_idx] = obj
        
        # Extract and add dependencies
        for obj in sql_objects:
            obj.dependencies = self.extractor.extract_dependencies(obj)
            
            # Add edges for dependencies
            obj_idx = self.node_map[obj.qualified_name.lower()]
            for dep in obj.dependencies:
                dep_lower = dep.lower()
                
                # Try with and without schema prefix
                if dep_lower in self.node_map:
                    dep_idx = self.node_map[dep_lower]
                    self.graph.add_edge(dep_idx, obj_idx, None)
                else:
                    # Try matching just the object name
                    for qualified_name, idx in self.node_map.items():
                        if qualified_name.endswith(f".{dep_lower}") or qualified_name == dep_lower:
                            self.graph.add_edge(idx, obj_idx, None)
                            break
        
        return self.graph
    
    def find_circular_dependencies(self) -> List[List[SQLObject]]:
        """Find all circular dependencies in the graph."""
        if not self.graph:
            return []
        
        cycles = []
        
        try:
            # Use rustworkx's cycle detection
            # First, check if graph is acyclic
            if not rx.is_directed_acyclic_graph(self.graph):
                # Find strongly connected components
                sccs = rx.strongly_connected_components(self.graph)
                
                # Filter out single-node components (not real cycles)
                for scc in sccs:
                    if len(scc) > 1:
                        cycle_objects = [self.reverse_map[idx] for idx in scc]
                        cycles.append(cycle_objects)
        
        except Exception as e:
            logger.error(f"Error detecting cycles: {e}")
        
        return cycles
    
    def get_dependency_order(self) -> List[SQLObject]:
        """Get objects in dependency order (topological sort)."""
        if not self.graph:
            return []
        
        try:
            # Get topological sort
            topo_indices = rx.topological_sort(self.graph)
            return [self.reverse_map[idx] for idx in topo_indices]
        
        except rx.DAGHasCycle:
            logger.warning("Graph has cycles, returning partial order")
            # Return objects in original order if cycles exist
            return list(self.reverse_map.values())
    
    def get_object_dependencies(self, obj_name: str) -> Dict[str, List[SQLObject]]:
        """Get direct and transitive dependencies for an object."""
        obj_name_lower = obj_name.lower()
        
        if obj_name_lower not in self.node_map:
            return {'direct': [], 'transitive': []}
        
        node_idx = self.node_map[obj_name_lower]
        
        # Get direct dependencies (predecessors)
        direct_indices = self.graph.predecessors(node_idx)
        direct_deps = [self.reverse_map[idx] for idx in direct_indices]
        
        # Get transitive dependencies using BFS
        transitive_indices = set()
        visited = set()
        queue = list(direct_indices)
        
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            
            visited.add(current)
            transitive_indices.add(current)
            
            # Add predecessors to queue
            for pred in self.graph.predecessors(current):
                if pred not in visited:
                    queue.append(pred)
        
        transitive_deps = [self.reverse_map[idx] for idx in transitive_indices]
        
        return {
            'direct': direct_deps,
            'transitive': transitive_deps
        }
    
    def get_object_dependents(self, obj_name: str) -> Dict[str, List[SQLObject]]:
        """Get objects that depend on this object."""
        obj_name_lower = obj_name.lower()
        
        if obj_name_lower not in self.node_map:
            return {'direct': [], 'transitive': []}
        
        node_idx = self.node_map[obj_name_lower]
        
        # Get direct dependents (successors)
        direct_indices = self.graph.successors(node_idx)
        direct_deps = [self.reverse_map[idx] for idx in direct_indices]
        
        # Get transitive dependents
        transitive_indices = set()
        visited = set()
        queue = list(direct_indices)
        
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            
            visited.add(current)
            transitive_indices.add(current)
            
            # Add successors to queue
            for succ in self.graph.successors(current):
                if succ not in visited:
                    queue.append(succ)
        
        transitive_deps = [self.reverse_map[idx] for idx in transitive_indices]
        
        return {
            'direct': direct_deps,
            'transitive': transitive_deps
        }
    
    def analyze_graph_metrics(self) -> Dict[str, Any]:
        """Analyze graph metrics and statistics."""
        if not self.graph:
            return {}
        
        metrics = {
            'node_count': self.graph.num_nodes(),
            'edge_count': self.graph.num_edges(),
            'is_acyclic': rx.is_directed_acyclic_graph(self.graph),
            'connected_components': len(rx.weakly_connected_components(self.graph)),
            'strongly_connected_components': len(rx.strongly_connected_components(self.graph)),
        }
        
        # Calculate degree statistics
        in_degrees = [self.graph.in_degree(i) for i in range(self.graph.num_nodes())]
        out_degrees = [self.graph.out_degree(i) for i in range(self.graph.num_nodes())]
        
        metrics['max_in_degree'] = max(in_degrees) if in_degrees else 0
        metrics['max_out_degree'] = max(out_degrees) if out_degrees else 0
        metrics['avg_in_degree'] = sum(in_degrees) / len(in_degrees) if in_degrees else 0
        metrics['avg_out_degree'] = sum(out_degrees) / len(out_degrees) if out_degrees else 0
        
        # Find hub objects (high out-degree)
        hub_threshold = metrics['avg_out_degree'] + 2  # 2 std devs above mean
        hubs = [
            self.reverse_map[i].qualified_name 
            for i in range(self.graph.num_nodes())
            if self.graph.out_degree(i) > hub_threshold
        ]
        metrics['hub_objects'] = hubs
        
        return metrics
    
    def export_to_dot(self) -> str:
        """Export dependency graph to DOT format for visualization."""
        if not self.graph:
            return ""
        
        dot_lines = ["digraph dependencies {"]
        dot_lines.append('  rankdir=LR;')
        dot_lines.append('  node [shape=box];')
        
        # Add nodes with labels
        for idx, obj in self.reverse_map.items():
            label = f"{obj.name}\\n[{obj.object_type}]"
            color = self._get_node_color(obj.object_type)
            dot_lines.append(f'  n{idx} [label="{label}", fillcolor="{color}", style=filled];')
        
        # Add edges
        for edge in self.graph.edge_list():
            dot_lines.append(f'  n{edge[0]} -> n{edge[1]};')
        
        dot_lines.append("}")
        
        return '\n'.join(dot_lines)
    
    def _get_node_color(self, object_type: str) -> str:
        """Get color for node based on object type."""
        colors = {
            'CREATE_TABLE': 'lightblue',
            'CREATE_VIEW': 'lightgreen',
            'CREATE_FUNCTION': 'lightyellow',
            'CREATE_TRIGGER': 'lightcoral',
            'CREATE_INDEX': 'lightgray',
            'CREATE_TYPE': 'lightpink',
        }
        return colors.get(object_type, 'white')