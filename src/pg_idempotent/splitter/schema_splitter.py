"""
Schema splitting module for organizing SQL objects into logical groups.

This module provides functionality to split SQL objects into separate schema
files based on dependencies, relationships, and logical grouping.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
import logging

from ..analyzer.rustworkx_analyzer import SQLObject, DependencyGraphAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class SchemaGroup:
    """Represents a group of related SQL objects."""
    
    name: str
    objects: List[SQLObject] = field(default_factory=list)
    description: Optional[str] = None
    
    def add_object(self, obj: SQLObject):
        """Add an object to this schema group."""
        if obj not in self.objects:
            self.objects.append(obj)
    
    @property
    def object_count(self) -> int:
        """Get count of objects in this group."""
        return len(self.objects)
    
    @property
    def object_types(self) -> Dict[str, int]:
        """Get distribution of object types."""
        type_counts = {}
        for obj in self.objects:
            type_counts[obj.object_type] = type_counts.get(obj.object_type, 0) + 1
        return type_counts
    
    def to_sql(self) -> str:
        """Convert group to SQL string."""
        sql_parts = []
        
        # Add header comment
        sql_parts.append(f"-- Schema: {self.name}")
        if self.description:
            sql_parts.append(f"-- Description: {self.description}")
        sql_parts.append(f"-- Objects: {self.object_count}")
        sql_parts.append("")
        
        # Group objects by type for better organization
        objects_by_type = {}
        for obj in self.objects:
            if obj.object_type not in objects_by_type:
                objects_by_type[obj.object_type] = []
            objects_by_type[obj.object_type].append(obj)
        
        # Add objects in a logical order
        type_order = [
            'CREATE_TYPE', 'CREATE_FUNCTION', 'CREATE_TABLE',
            'CREATE_VIEW', 'CREATE_INDEX', 'CREATE_TRIGGER',
            'CREATE_POLICY', 'GRANT'
        ]
        
        for obj_type in type_order:
            if obj_type in objects_by_type:
                sql_parts.append(f"\n-- {obj_type} objects")
                sql_parts.append("-" * 60)
                
                for obj in objects_by_type[obj_type]:
                    sql_parts.append(f"\n{obj.raw_sql}")
                    if not obj.raw_sql.rstrip().endswith(';'):
                        sql_parts.append(';')
        
        # Add any remaining types
        for obj_type, objects in objects_by_type.items():
            if obj_type not in type_order:
                sql_parts.append(f"\n-- {obj_type} objects")
                sql_parts.append("-" * 60)
                
                for obj in objects:
                    sql_parts.append(f"\n{obj.raw_sql}")
                    if not obj.raw_sql.rstrip().endswith(';'):
                        sql_parts.append(';')
        
        return '\n'.join(sql_parts)


class SchemaSplitter:
    """Split SQL objects into logical schema groups."""
    
    def __init__(self, max_objects_per_schema: int = 50):
        self.max_objects_per_schema = max_objects_per_schema
        self.analyzer = DependencyGraphAnalyzer()
    
    def split_objects(
        self, 
        sql_objects: List[SQLObject],
        schema_assignments: Optional[Dict[str, str]] = None
    ) -> List[SchemaGroup]:
        """Split SQL objects into schema groups."""
        if not sql_objects:
            return []
        
        # Build dependency graph
        self.analyzer.build_dependency_graph(sql_objects)
        
        # Use provided schema assignments or auto-generate
        if schema_assignments:
            return self._split_by_assignments(sql_objects, schema_assignments)
        else:
            return self._split_by_dependencies(sql_objects)
    
    def _split_by_assignments(
        self, 
        sql_objects: List[SQLObject],
        schema_assignments: Dict[str, str]
    ) -> List[SchemaGroup]:
        """Split objects based on provided schema assignments."""
        groups = {}
        
        for obj in sql_objects:
            schema_name = schema_assignments.get(obj.name, 'unassigned')
            
            if schema_name not in groups:
                groups[schema_name] = SchemaGroup(name=schema_name)
            
            groups[schema_name].add_object(obj)
        
        # Sort objects within each group by dependencies
        for group in groups.values():
            group.objects = self._sort_by_dependencies(group.objects)
        
        return list(groups.values())
    
    def _split_by_dependencies(self, sql_objects: List[SQLObject]) -> List[SchemaGroup]:
        """Split objects based on dependency analysis."""
        # Find strongly connected components
        try:
            import rustworkx as rx
            sccs = rx.strongly_connected_components(self.analyzer.graph)
        except Exception as e:
            logger.warning(f"Failed to analyze dependencies: {e}")
            # Fall back to simple splitting
            return self._split_by_size(sql_objects)
        
        groups = []
        assigned_objects = set()
        
        # Create groups for each strongly connected component
        for i, scc in enumerate(sccs):
            if len(scc) > 1:  # Only create groups for actual components
                group = SchemaGroup(
                    name=f"component_{i}",
                    description="Strongly connected objects"
                )
                
                for node_idx in scc:
                    obj = self.analyzer.reverse_map[node_idx]
                    group.add_object(obj)
                    assigned_objects.add(obj)
                
                groups.append(group)
        
        # Group remaining objects by their dependencies
        unassigned = [obj for obj in sql_objects if obj not in assigned_objects]
        
        # Use clustering based on shared dependencies
        clusters = self._cluster_by_dependencies(unassigned)
        
        for i, cluster in enumerate(clusters):
            group = SchemaGroup(
                name=f"cluster_{i}",
                description="Related objects"
            )
            for obj in cluster:
                group.add_object(obj)
            groups.append(group)
        
        # Merge small groups if needed
        groups = self._merge_small_groups(groups)
        
        # Sort objects within each group
        for group in groups:
            group.objects = self._sort_by_dependencies(group.objects)
        
        return groups
    
    def _split_by_size(self, sql_objects: List[SQLObject]) -> List[SchemaGroup]:
        """Simple splitting based on size limits."""
        groups = []
        current_group = None
        
        for obj in sql_objects:
            if not current_group or current_group.object_count >= self.max_objects_per_schema:
                current_group = SchemaGroup(name=f"schema_{len(groups)}")
                groups.append(current_group)
            
            current_group.add_object(obj)
        
        return groups
    
    def _cluster_by_dependencies(self, sql_objects: List[SQLObject]) -> List[List[SQLObject]]:
        """Cluster objects based on shared dependencies."""
        clusters = []
        obj_to_cluster = {}
        
        for obj in sql_objects:
            # Find objects that share dependencies
            best_cluster = None
            best_score = 0
            
            for i, cluster in enumerate(clusters):
                score = self._calculate_cluster_affinity(obj, cluster)
                if score > best_score:
                    best_score = score
                    best_cluster = i
            
            if best_cluster is not None and best_score > 0.3:  # Threshold
                clusters[best_cluster].append(obj)
                obj_to_cluster[obj] = best_cluster
            else:
                # Create new cluster
                clusters.append([obj])
                obj_to_cluster[obj] = len(clusters) - 1
        
        return clusters
    
    def _calculate_cluster_affinity(self, obj: SQLObject, cluster: List[SQLObject]) -> float:
        """Calculate affinity score between object and cluster."""
        if not cluster:
            return 0.0
        
        # Calculate based on shared dependencies
        obj_deps = obj.dependencies
        if not obj_deps:
            return 0.0
        
        shared_deps = 0
        total_deps = len(obj_deps)
        
        for cluster_obj in cluster:
            shared = obj_deps.intersection(cluster_obj.dependencies)
            shared_deps += len(shared)
        
        # Also check if objects depend on each other
        cluster_names = {co.qualified_name.lower() for co in cluster}
        if obj.qualified_name.lower() in cluster_names:
            shared_deps += 5  # Boost score for direct dependencies
        
        # Check if this object depends on cluster objects
        for dep in obj_deps:
            if dep.lower() in cluster_names:
                shared_deps += 2
        
        return shared_deps / (total_deps + len(cluster))
    
    def _merge_small_groups(self, groups: List[SchemaGroup]) -> List[SchemaGroup]:
        """Merge small groups to avoid too many schemas."""
        MIN_GROUP_SIZE = 3
        
        # Separate small and large groups
        small_groups = [g for g in groups if g.object_count < MIN_GROUP_SIZE]
        large_groups = [g for g in groups if g.object_count >= MIN_GROUP_SIZE]
        
        # Merge small groups
        if small_groups:
            merged = SchemaGroup(name="misc", description="Miscellaneous objects")
            for group in small_groups:
                for obj in group.objects:
                    merged.add_object(obj)
            
            # Only add if it has objects
            if merged.object_count > 0:
                large_groups.append(merged)
        
        return large_groups
    
    def _sort_by_dependencies(self, objects: List[SQLObject]) -> List[SQLObject]:
        """Sort objects by their dependencies."""
        # Build a subgraph for these objects
        object_set = set(objects)
        object_names = {obj.qualified_name.lower() for obj in objects}
        
        # Simple topological sort
        sorted_objects = []
        remaining = objects.copy()
        
        while remaining:
            # Find objects with no dependencies in the remaining set
            ready = []
            for obj in remaining:
                deps_in_set = obj.dependencies.intersection(object_names)
                if not deps_in_set or all(
                    dep not in {o.qualified_name.lower() for o in remaining}
                    for dep in deps_in_set
                ):
                    ready.append(obj)
            
            if not ready:
                # Circular dependency, just add remaining
                sorted_objects.extend(remaining)
                break
            
            # Add ready objects and remove from remaining
            sorted_objects.extend(ready)
            for obj in ready:
                remaining.remove(obj)
        
        return sorted_objects
    
    def write_schema_files(
        self, 
        groups: List[SchemaGroup],
        output_dir: str,
        file_prefix: str = "schema"
    ) -> Dict[str, str]:
        """Write schema groups to separate files."""
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)
        
        written_files = {}
        
        for i, group in enumerate(groups):
            filename = f"{file_prefix}_{group.name}.sql"
            filepath = output_dir_path / filename
            
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(group.to_sql())
                
                written_files[group.name] = str(filepath)
                logger.info(f"Wrote {group.object_count} objects to {filepath}")
                
            except Exception as e:
                logger.error(f"Failed to write schema file {filepath}: {e}")
        
        # Write index file
        index_file = output_dir_path / f"{file_prefix}_index.sql"
        try:
            with open(index_file, 'w', encoding='utf-8') as f:
                f.write("-- Schema Index File\n")
                f.write("-- Load schemas in dependency order\n\n")
                
                for group in groups:
                    filename = f"{file_prefix}_{group.name}.sql"
                    f.write(f"\\i {filename}\n")
            
            written_files['_index'] = str(index_file)
            
        except Exception as e:
            logger.error(f"Failed to write index file: {e}")
        
        return written_files
    
    def generate_schema_report(self, groups: List[SchemaGroup]) -> str:
        """Generate a report about the schema split."""
        report_lines = [
            "Schema Split Report",
            "=" * 50,
            f"Total objects: {sum(g.object_count for g in groups)}",
            f"Number of schemas: {len(groups)}",
            ""
        ]
        
        for group in groups:
            report_lines.extend([
                f"\nSchema: {group.name}",
                "-" * 30,
                f"Objects: {group.object_count}"
            ])
            
            if group.description:
                report_lines.append(f"Description: {group.description}")
            
            # Object type breakdown
            report_lines.append("\nObject types:")
            for obj_type, count in group.object_types.items():
                report_lines.append(f"  - {obj_type}: {count}")
            
            # List objects
            report_lines.append("\nObjects:")
            for obj in group.objects[:10]:  # Show first 10
                report_lines.append(f"  - {obj.qualified_name} ({obj.object_type})")
            
            if group.object_count > 10:
                report_lines.append(f"  ... and {group.object_count - 10} more")
        
        return '\n'.join(report_lines)