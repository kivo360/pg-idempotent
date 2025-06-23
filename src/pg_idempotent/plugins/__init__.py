"""
Plugin system for pg-idempotent.

This module provides a flexible plugin architecture for extending
pg-idempotent functionality.
"""

from .base import (
    Plugin,
    ParserPlugin,
    TransformerPlugin,
    ValidatorPlugin,
    AnalyzerPlugin,
    OutputPlugin,
    PluginInfo,
    PluginType,
    PluginRegistry,
    registry
)

from .loader import (
    PluginLoader,
    load_plugins,
    load_plugin,
    reload_plugin,
    get_loaded_plugins,
    get_plugins_by_type
)

__all__ = [
    # Base classes
    "Plugin",
    "ParserPlugin",
    "TransformerPlugin",
    "ValidatorPlugin",
    "AnalyzerPlugin",
    "OutputPlugin",
    
    # Data classes
    "PluginInfo",
    "PluginType",
    
    # Registry
    "PluginRegistry",
    "registry",
    
    # Loader
    "PluginLoader",
    "load_plugins",
    "load_plugin",
    "reload_plugin",
    "get_loaded_plugins",
    "get_plugins_by_type"
]