"""
Base classes for pg-idempotent plugin system.

This module defines the base classes and interfaces that plugins must implement
to extend pg-idempotent functionality.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type
from enum import Enum
import logging

from ..parser.parser import ParsedStatement
from ..transformer.transformer import TransformationResult

logger = logging.getLogger(__name__)


class PluginType(Enum):
    """Types of plugins supported."""
    PARSER = "parser"
    TRANSFORMER = "transformer"
    VALIDATOR = "validator"
    ANALYZER = "analyzer"
    OUTPUT = "output"


@dataclass
class PluginInfo:
    """Information about a plugin."""
    
    name: str
    version: str
    description: str
    author: Optional[str] = None
    plugin_type: PluginType = PluginType.TRANSFORMER
    capabilities: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate plugin info."""
        if not self.name:
            raise ValueError("Plugin must have a name")
        if not self.version:
            raise ValueError("Plugin must have a version")


class Plugin(ABC):
    """Base class for all plugins."""
    
    def __init__(self):
        self._enabled = True
        self._config = {}
    
    @property
    @abstractmethod
    def info(self) -> PluginInfo:
        """Get plugin information."""
        pass
    
    @property
    def enabled(self) -> bool:
        """Check if plugin is enabled."""
        return self._enabled
    
    def enable(self):
        """Enable the plugin."""
        self._enabled = True
        logger.info(f"Plugin '{self.info.name}' enabled")
    
    def disable(self):
        """Disable the plugin."""
        self._enabled = False
        logger.info(f"Plugin '{self.info.name}' disabled")
    
    def configure(self, config: Dict[str, Any]):
        """Configure the plugin."""
        self._config.update(config)
        logger.info(f"Plugin '{self.info.name}' configured with: {config}")
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(key, default)
    
    @abstractmethod
    def initialize(self):
        """Initialize the plugin."""
        pass
    
    def cleanup(self):
        """Clean up plugin resources."""
        pass


class ParserPlugin(Plugin):
    """Base class for parser plugins."""
    
    @abstractmethod
    def can_parse(self, sql: str) -> bool:
        """Check if this plugin can parse the given SQL."""
        pass
    
    @abstractmethod
    def parse(self, sql: str) -> List[ParsedStatement]:
        """Parse SQL statements."""
        pass
    
    def pre_parse(self, sql: str) -> str:
        """Pre-process SQL before parsing."""
        return sql
    
    def post_parse(self, statements: List[ParsedStatement]) -> List[ParsedStatement]:
        """Post-process parsed statements."""
        return statements


class TransformerPlugin(Plugin):
    """Base class for transformer plugins."""
    
    @abstractmethod
    def can_transform(self, statement: ParsedStatement) -> bool:
        """Check if this plugin can transform the given statement."""
        pass
    
    @abstractmethod
    def transform(self, statement: ParsedStatement) -> str:
        """Transform a single statement."""
        pass
    
    def pre_transform(self, statements: List[ParsedStatement]) -> List[ParsedStatement]:
        """Pre-process statements before transformation."""
        return statements
    
    def post_transform(self, result: TransformationResult) -> TransformationResult:
        """Post-process transformation result."""
        return result
    
    def get_priority(self) -> int:
        """Get plugin priority (higher = runs first)."""
        return 50


class ValidatorPlugin(Plugin):
    """Base class for validator plugins."""
    
    @abstractmethod
    def validate(self, sql: str, transformed_sql: str) -> Dict[str, Any]:
        """Validate transformation."""
        pass
    
    def can_validate(self, sql: str) -> bool:
        """Check if this plugin can validate the given SQL."""
        return True
    
    def get_validation_level(self) -> str:
        """Get validation level (error, warning, info)."""
        return "error"


class AnalyzerPlugin(Plugin):
    """Base class for analyzer plugins."""
    
    @abstractmethod
    def analyze(self, statements: List[ParsedStatement]) -> Dict[str, Any]:
        """Analyze SQL statements."""
        pass
    
    def can_analyze(self, statement_type: str) -> bool:
        """Check if this plugin can analyze the given statement type."""
        return True
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get analysis metrics."""
        return {}


class OutputPlugin(Plugin):
    """Base class for output plugins."""
    
    @abstractmethod
    def write(self, result: TransformationResult, output_path: str):
        """Write transformation result."""
        pass
    
    def can_write(self, output_format: str) -> bool:
        """Check if this plugin can write the given format."""
        return True
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported output formats."""
        return []


class PluginRegistry:
    """Registry for managing plugins."""
    
    def __init__(self):
        self._plugins: Dict[str, Plugin] = {}
        self._type_map: Dict[PluginType, List[str]] = {
            plugin_type: [] for plugin_type in PluginType
        }
    
    def register(self, plugin: Plugin):
        """Register a plugin."""
        info = plugin.info
        
        if info.name in self._plugins:
            raise ValueError(f"Plugin '{info.name}' already registered")
        
        self._plugins[info.name] = plugin
        self._type_map[info.plugin_type].append(info.name)
        
        logger.info(f"Registered plugin '{info.name}' (type: {info.plugin_type.value})")
    
    def unregister(self, name: str):
        """Unregister a plugin."""
        if name not in self._plugins:
            raise ValueError(f"Plugin '{name}' not found")
        
        plugin = self._plugins[name]
        plugin_type = plugin.info.plugin_type
        
        del self._plugins[name]
        self._type_map[plugin_type].remove(name)
        
        logger.info(f"Unregistered plugin '{name}'")
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name."""
        return self._plugins.get(name)
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[Plugin]:
        """Get all plugins of a specific type."""
        plugin_names = self._type_map.get(plugin_type, [])
        return [self._plugins[name] for name in plugin_names if self._plugins[name].enabled]
    
    def get_all_plugins(self) -> List[Plugin]:
        """Get all registered plugins."""
        return list(self._plugins.values())
    
    def enable_plugin(self, name: str):
        """Enable a plugin."""
        plugin = self.get_plugin(name)
        if plugin:
            plugin.enable()
        else:
            raise ValueError(f"Plugin '{name}' not found")
    
    def disable_plugin(self, name: str):
        """Disable a plugin."""
        plugin = self.get_plugin(name)
        if plugin:
            plugin.disable()
        else:
            raise ValueError(f"Plugin '{name}' not found")
    
    def configure_plugin(self, name: str, config: Dict[str, Any]):
        """Configure a plugin."""
        plugin = self.get_plugin(name)
        if plugin:
            plugin.configure(config)
        else:
            raise ValueError(f"Plugin '{name}' not found")
    
    def initialize_all(self):
        """Initialize all plugins."""
        for plugin in self._plugins.values():
            try:
                plugin.initialize()
                logger.info(f"Initialized plugin '{plugin.info.name}'")
            except Exception as e:
                logger.error(f"Failed to initialize plugin '{plugin.info.name}': {e}")
                plugin.disable()
    
    def cleanup_all(self):
        """Clean up all plugins."""
        for plugin in self._plugins.values():
            try:
                plugin.cleanup()
                logger.info(f"Cleaned up plugin '{plugin.info.name}'")
            except Exception as e:
                logger.error(f"Failed to cleanup plugin '{plugin.info.name}': {e}")


# Global plugin registry
registry = PluginRegistry()