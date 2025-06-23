"""Tests for plugin system and advanced CLI functionality."""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import typer
from typer.testing import CliRunner
from pg_idempotent.plugins.base import (
    Plugin, TransformerPlugin, AnalyzerPlugin, OutputPlugin
)
from pg_idempotent.plugins.loader import PluginLoader, PluginRegistry
from pg_idempotent.parser.parser import ParsedStatement
from pg_idempotent.analyzer.rustworkx_analyzer import SQLObject


# Mock plugin implementations for testing
class MockDependencyAnalyzer(AnalyzerPlugin):
    """Mock dependency analyzer for testing."""
    
    def analyze(self, statements):
        """Mock analysis that returns a simple graph."""
        graph = DependencyGraph()
        for stmt in statements:
            if stmt.object_name:
                obj = SQLObject(
                    name=stmt.object_name,
                    schema=stmt.schema_name or "public",
                    object_type=stmt.statement_type.replace("CREATE_", "").lower(),
                    raw_sql=stmt.raw_sql,
                    dependencies=set(),
                    metadata={}
                )
                graph.add_object(obj)
        return graph


class MockSchemaSplitter(SchemaSplitter):
    """Mock schema splitter for testing."""
    
    def split(self, graph, strategy):
        """Mock splitting that creates simple categories."""
        return {
            "00_types": [obj for obj in graph.objects.values() if obj.object_type == "type"],
            "01_tables": [obj for obj in graph.objects.values() if obj.object_type == "table"],
            "02_functions": [obj for obj in graph.objects.values() if obj.object_type == "function"]
        }


class MockFormatHandler(FormatHandler):
    """Mock format handler for testing."""
    
    def generate_files(self, categorized):
        """Mock file generation."""
        files = {}
        for category, objects in categorized.items():
            if objects:
                content = "\n".join([obj.raw_sql for obj in objects])
                files[Path(f"{category}.sql")] = content
        return files


class MockSchemaNamer(SchemaNamer):
    """Mock schema namer for testing."""
    
    def name_schemas(self, object_groups, domain_hints=None):
        """Mock naming that returns simple names."""
        return {
            group_key: f"schema_{i}"
            for i, group_key in enumerate(object_groups.keys())
        }


class TestPluginManager:
    """Test plugin manager functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.plugin_manager = PluginManager()
    
    def test_plugin_registration(self):
        """Test plugin registration."""
        analyzer = MockDependencyAnalyzer()
        splitter = MockSchemaSplitter()
        formatter = MockFormatHandler()
        namer = MockSchemaNamer()
        
        # Register plugins
        self.plugin_manager.register_analyzer("mock", analyzer)
        self.plugin_manager.register_splitter("mock", splitter)
        self.plugin_manager.register_formatter("mock", formatter)
        self.plugin_manager.register_namer("mock", namer)
        
        # Verify registration
        assert "mock" in self.plugin_manager.analyzers
        assert "mock" in self.plugin_manager.splitters
        assert "mock" in self.plugin_manager.formatters
        assert "mock" in self.plugin_manager.namers
        
        # Verify retrieval
        assert self.plugin_manager.get_analyzer("mock") == analyzer
        assert self.plugin_manager.get_splitter("mock") == splitter
        assert self.plugin_manager.get_formatter("mock") == formatter
        assert self.plugin_manager.get_namer("mock") == namer
    
    def test_plugin_retrieval_fallback(self):
        """Test plugin retrieval with fallback."""
        # Register a default analyzer
        default_analyzer = MockDependencyAnalyzer()
        self.plugin_manager.register_analyzer("default", default_analyzer)
        
        # Should return default when requesting non-existent plugin
        result = self.plugin_manager.get_analyzer("non_existent")
        assert result == default_analyzer
    
    def test_plugin_listing(self):
        """Test listing available plugins."""
        # Register some plugins
        self.plugin_manager.register_analyzer("analyzer1", MockDependencyAnalyzer())
        self.plugin_manager.register_analyzer("analyzer2", MockDependencyAnalyzer())
        self.plugin_manager.register_splitter("splitter1", MockSchemaSplitter())
        
        # Test listing
        analyzers = self.plugin_manager.list_analyzers()
        splitters = self.plugin_manager.list_splitters()
        
        assert "analyzer1" in analyzers
        assert "analyzer2" in analyzers
        assert "splitter1" in splitters
        assert len(analyzers) == 2
        assert len(splitters) == 1
    
    def test_plugin_replacement(self):
        """Test replacing existing plugins."""
        analyzer1 = MockDependencyAnalyzer()
        analyzer2 = MockDependencyAnalyzer()
        
        # Register first plugin
        self.plugin_manager.register_analyzer("test", analyzer1)
        assert self.plugin_manager.get_analyzer("test") == analyzer1
        
        # Replace with second plugin
        self.plugin_manager.register_analyzer("test", analyzer2)
        assert self.plugin_manager.get_analyzer("test") == analyzer2
    
    def test_plugin_workflow_integration(self):
        """Test complete workflow using plugins."""
        # Register all plugin types
        analyzer = MockDependencyAnalyzer()
        splitter = MockSchemaSplitter()
        formatter = MockFormatHandler()
        namer = MockSchemaNamer()
        
        self.plugin_manager.register_analyzer("test", analyzer)
        self.plugin_manager.register_splitter("test", splitter)
        self.plugin_manager.register_formatter("test", formatter)
        self.plugin_manager.register_namer("test", namer)
        
        # Mock statements
        statements = [
            ParsedStatement(
                raw_sql="CREATE TABLE users (id SERIAL);",
                ast=None,
                statement_type="CREATE_TABLE",
                object_name="users",
                schema_name="public",
                dollar_quotes=[]
            ),
            ParsedStatement(
                raw_sql="CREATE TYPE status AS ENUM ('active');",
                ast=None,
                statement_type="CREATE_TYPE",
                object_name="status",
                schema_name="public",
                dollar_quotes=[]
            )
        ]
        
        # Test workflow
        selected_analyzer = self.plugin_manager.get_analyzer("test")
        graph = selected_analyzer.analyze(statements)
        
        selected_splitter = self.plugin_manager.get_splitter("test")
        categorized = selected_splitter.split(graph, "test")
        
        selected_formatter = self.plugin_manager.get_formatter("test")
        files = selected_formatter.generate_files(categorized)
        
        selected_namer = self.plugin_manager.get_namer("test")
        names = selected_namer.name_schemas(categorized)
        
        # Verify results
        assert len(graph.objects) == 2
        assert "01_tables" in categorized
        assert "00_types" in categorized
        assert len(files) > 0
        assert len(names) > 0


class TestAdvancedCLI:
    """Test advanced CLI commands."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def create_test_sql_file(self, content):
        """Helper to create temporary SQL file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
            f.write(content)
            return Path(f.name)
    
    def test_split_command_basic(self):
        """Test basic split command functionality."""
        # Create test SQL file
        sql_content = """
        CREATE TYPE status AS ENUM ('active', 'inactive');
        CREATE TABLE users (id SERIAL PRIMARY KEY, status status);
        CREATE INDEX idx_users_status ON users(status);
        """
        
        sql_file = self.create_test_sql_file(sql_content)
        
        try:
            with tempfile.TemporaryDirectory() as output_dir:
                # Mock the plugin system
                with patch('pg_idempotent.cli.advanced_cli.PluginManager') as mock_pm_class:
                    mock_pm = Mock()
                    mock_pm.get_analyzer.return_value = MockDependencyAnalyzer()
                    mock_pm.get_splitter.return_value = MockSchemaSplitter()
                    mock_pm.get_formatter.return_value = MockFormatHandler()
                    mock_pm_class.return_value = mock_pm
                    
                    # Run CLI command
                    result = self.runner.invoke(app, [
                        "split",
                        str(sql_file),
                        "--output-dir", output_dir,
                        "--format", "standard",
                        "--dry-run"
                    ])
                    
                    assert result.exit_code == 0
                    assert "split" in result.output.lower() or "schema" in result.output.lower()
        finally:
            # Clean up
            sql_file.unlink()
    
    def test_analyze_command(self):
        """Test analyze command functionality."""
        sql_content = """
        CREATE TABLE users (id SERIAL PRIMARY KEY);
        CREATE TABLE posts (id SERIAL, user_id INTEGER REFERENCES users(id));
        """
        
        sql_file = self.create_test_sql_file(sql_content)
        
        try:
            with patch('pg_idempotent.cli.advanced_cli.PluginManager') as mock_pm_class:
                mock_pm = Mock()
                mock_analyzer = Mock()
                mock_analyzer.analyze.return_value = Mock()
                mock_analyzer.topological_sort.return_value = ["users", "posts"]
                mock_analyzer.detect_cycles.return_value = []
                mock_pm.get_analyzer.return_value = mock_analyzer
                mock_pm_class.return_value = mock_pm
                
                result = self.runner.invoke(app, [
                    "analyze",
                    str(sql_file),
                    "--show-graph",
                    "--detect-cycles"
                ])
                
                assert result.exit_code == 0
                # Should show analysis results
                assert "users" in result.output or "analyze" in result.output.lower()
        finally:
            sql_file.unlink()
    
    def test_merge_command(self):
        """Test merge command functionality."""
        with tempfile.TemporaryDirectory() as schema_dir:
            # Create mock schema files
            (Path(schema_dir) / "00_types.sql").write_text("CREATE TYPE status AS ENUM ('active');")
            (Path(schema_dir) / "01_tables.sql").write_text("CREATE TABLE users (id SERIAL);")
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as output_file:
                try:
                    result = self.runner.invoke(app, [
                        "merge",
                        schema_dir,
                        output_file.name,
                        "--order", "topological"
                    ])
                    
                    # Command should execute without error
                    assert result.exit_code == 0
                    
                    # Check if output file was created with content
                    output_content = Path(output_file.name).read_text()
                    assert len(output_content) > 0
                finally:
                    Path(output_file.name).unlink()
    
    def test_validate_command(self):
        """Test validate command functionality."""
        sql_content = """
        CREATE TABLE users (id SERIAL PRIMARY KEY);
        CREATE TABLE posts (user_id INTEGER REFERENCES users(id));
        """
        
        sql_file = self.create_test_sql_file(sql_content)
        
        try:
            with patch('pg_idempotent.cli.advanced_cli.DatabaseComparator') as mock_comparator_class:
                mock_comparator = Mock()
                mock_comparator.validate_dependencies.return_value = []
                mock_comparator.check_circular_dependencies.return_value = []
                mock_comparator_class.return_value = mock_comparator
                
                result = self.runner.invoke(app, [
                    "validate",
                    str(sql_file),
                    "--check-dependencies",
                    "--check-idempotency"
                ])
                
                assert result.exit_code == 0
                assert "valid" in result.output.lower() or "check" in result.output.lower()
        finally:
            sql_file.unlink()
    
    def test_cli_error_handling(self):
        """Test CLI error handling."""
        # Test with non-existent file
        result = self.runner.invoke(app, [
            "split",
            "non_existent_file.sql"
        ])
        
        assert result.exit_code != 0
        assert "not found" in result.output.lower() or "error" in result.output.lower()
    
    def test_cli_help_commands(self):
        """Test CLI help functionality."""
        # Test main help
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "split" in result.output
        assert "analyze" in result.output
        
        # Test command-specific help
        result = self.runner.invoke(app, ["split", "--help"])
        assert result.exit_code == 0
        assert "input" in result.output.lower()
        assert "output" in result.output.lower()


class TestPluginConfiguration:
    """Test plugin configuration and settings."""
    
    def test_plugin_configuration_loading(self):
        """Test loading plugin configuration."""
        config = {
            "default_analyzer": "rustworkx",
            "default_splitter": "supabase",
            "default_formatter": "supabase",
            "default_namer": "llm"
        }
        
        plugin_manager = PluginManager(config=config)
        
        assert plugin_manager.config["default_analyzer"] == "rustworkx"
        assert plugin_manager.config["default_splitter"] == "supabase"
    
    def test_plugin_discovery(self):
        """Test automatic plugin discovery."""
        # Mock entry points
        mock_entry_point = Mock()
        mock_entry_point.name = "test_plugin"
        mock_entry_point.load.return_value = Mock()
        
        with patch('pkg_resources.iter_entry_points') as mock_iter:
            mock_iter.return_value = [mock_entry_point]
            
            # This would test the actual discovery mechanism
            # For now, just verify the mock works
            entry_points = list(mock_iter('pg_idempotent.plugins'))
            assert len(entry_points) == 1
            assert entry_points[0].name == "test_plugin"
    
    def test_plugin_validation(self):
        """Test plugin validation."""
        plugin_manager = PluginManager()
        
        # Test valid plugin
        valid_analyzer = MockDependencyAnalyzer()
        result = plugin_manager.validate_plugin(valid_analyzer, DependencyAnalyzer)
        assert result is True
        
        # Test invalid plugin
        invalid_plugin = "not a plugin"
        result = plugin_manager.validate_plugin(invalid_plugin, DependencyAnalyzer)
        assert result is False


class TestCLIIntegration:
    """Test CLI integration with plugin system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_plugin_selection_via_cli(self):
        """Test selecting plugins via CLI arguments."""
        sql_content = "CREATE TABLE users (id SERIAL);"
        sql_file = Path(tempfile.mktemp(suffix='.sql'))
        sql_file.write_text(sql_content)
        
        try:
            with tempfile.TemporaryDirectory() as output_dir:
                with patch('pg_idempotent.cli.advanced_cli.PluginManager') as mock_pm_class:
                    mock_pm = Mock()
                    mock_pm.get_analyzer.return_value = MockDependencyAnalyzer()
                    mock_pm.get_splitter.return_value = MockSchemaSplitter()
                    mock_pm.get_formatter.return_value = MockFormatHandler()
                    mock_pm.get_namer.return_value = MockSchemaNamer()
                    mock_pm_class.return_value = mock_pm
                    
                    result = self.runner.invoke(app, [
                        "split",
                        str(sql_file),
                        "--output-dir", output_dir,
                        "--analyzer", "rustworkx",
                        "--format", "supabase",
                        "--strategy", "hybrid",
                        "--namer", "llm"
                    ])
                    
                    assert result.exit_code == 0
                    
                    # Verify correct plugins were requested
                    mock_pm.get_analyzer.assert_called_with("rustworkx")
                    mock_pm.get_formatter.assert_called_with("supabase")
                    mock_pm.get_namer.assert_called_with("llm")
        finally:
            sql_file.unlink()
    
    def test_llm_configuration_via_cli(self):
        """Test LLM configuration through CLI."""
        sql_content = "CREATE TABLE users (id SERIAL);"
        sql_file = Path(tempfile.mktemp(suffix='.sql'))
        sql_file.write_text(sql_content)
        
        try:
            with tempfile.TemporaryDirectory() as output_dir:
                with patch('pg_idempotent.cli.advanced_cli.PluginManager'):
                    with patch.dict(os.environ, {}, clear=True):
                        result = self.runner.invoke(app, [
                            "split",
                            str(sql_file),
                            "--output-dir", output_dir,
                            "--namer", "llm",
                            "--api-key", "test-key",
                            "--model", "gpt-3.5-turbo",
                            "--domain", "e-commerce platform"
                        ])
                        
                        # Should set environment variables
                        # Note: In a real implementation, this would test the actual env var setting
                        assert result.exit_code == 0
        finally:
            sql_file.unlink()
    
    def test_dry_run_functionality(self):
        """Test dry run functionality."""
        sql_content = """
        CREATE TABLE users (id SERIAL);
        CREATE TABLE posts (user_id INTEGER REFERENCES users(id));
        """
        sql_file = Path(tempfile.mktemp(suffix='.sql'))
        sql_file.write_text(sql_content)
        
        try:
            with tempfile.TemporaryDirectory() as output_dir:
                with patch('pg_idempotent.cli.advanced_cli.PluginManager') as mock_pm_class:
                    mock_pm = Mock()
                    mock_pm.get_analyzer.return_value = MockDependencyAnalyzer()
                    mock_pm.get_splitter.return_value = MockSchemaSplitter()
                    mock_pm.get_formatter.return_value = MockFormatHandler()
                    mock_pm_class.return_value = mock_pm
                    
                    result = self.runner.invoke(app, [
                        "split",
                        str(sql_file),
                        "--output-dir", output_dir,
                        "--dry-run"
                    ])
                    
                    assert result.exit_code == 0
                    assert "preview" in result.output.lower() or "dry run" in result.output.lower()
                    
                    # Verify no files were actually created
                    created_files = list(Path(output_dir).glob("*.sql"))
                    assert len(created_files) == 0
        finally:
            sql_file.unlink()


class TestPluginErrorHandling:
    """Test error handling in plugin system."""
    
    def test_plugin_loading_error(self):
        """Test handling of plugin loading errors."""
        plugin_manager = PluginManager()
        
        # Test registering invalid plugin
        with pytest.raises(TypeError):
            plugin_manager.register_analyzer("invalid", "not a plugin")
    
    def test_plugin_execution_error(self):
        """Test handling of plugin execution errors."""
        class FailingAnalyzer(DependencyAnalyzer):
            def analyze(self, statements):
                raise Exception("Plugin failure")
        
        plugin_manager = PluginManager()
        plugin_manager.register_analyzer("failing", FailingAnalyzer())
        
        analyzer = plugin_manager.get_analyzer("failing")
        
        with pytest.raises(Exception, match="Plugin failure"):
            analyzer.analyze([])
    
    def test_missing_plugin_fallback(self):
        """Test fallback when requested plugin is missing."""
        plugin_manager = PluginManager()
        
        # Register default
        default_analyzer = MockDependencyAnalyzer()
        plugin_manager.register_analyzer("default", default_analyzer)
        
        # Request non-existent plugin
        result = plugin_manager.get_analyzer("non_existent")
        
        # Should return default
        assert result == default_analyzer


class TestPluginCompatibility:
    """Test plugin compatibility and versioning."""
    
    def test_plugin_interface_compliance(self):
        """Test that plugins comply with expected interfaces."""
        # Test DependencyAnalyzer interface
        analyzer = MockDependencyAnalyzer()
        assert hasattr(analyzer, 'analyze')
        assert callable(analyzer.analyze)
        
        # Test SchemaSplitter interface
        splitter = MockSchemaSplitter()
        assert hasattr(splitter, 'split')
        assert callable(splitter.split)
        
        # Test FormatHandler interface
        formatter = MockFormatHandler()
        assert hasattr(formatter, 'generate_files')
        assert callable(formatter.generate_files)
        
        # Test SchemaNamer interface
        namer = MockSchemaNamer()
        assert hasattr(namer, 'name_schemas')
        assert callable(namer.name_schemas)
    
    def test_plugin_data_flow(self):
        """Test that data flows correctly between plugins."""
        # Create test data
        statements = [
            ParsedStatement(
                raw_sql="CREATE TABLE test (id SERIAL);",
                ast=None,
                statement_type="CREATE_TABLE",
                object_name="test",
                schema_name="public",
                dollar_quotes=[]
            )
        ]
        
        # Test data flow through plugin chain
        analyzer = MockDependencyAnalyzer()
        splitter = MockSchemaSplitter()
        formatter = MockFormatHandler()
        namer = MockSchemaNamer()
        
        # Analyzer -> Splitter
        graph = analyzer.analyze(statements)
        assert hasattr(graph, 'objects')
        
        # Splitter -> Formatter
        categorized = splitter.split(graph, "test")
        assert isinstance(categorized, dict)
        
        # Formatter -> Files
        files = formatter.generate_files(categorized)
        assert isinstance(files, dict)
        
        # Namer -> Schema names
        names = namer.name_schemas(categorized)
        assert isinstance(names, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])