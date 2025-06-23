"""
Plugin loader for pg-idempotent.

This module provides functionality to dynamically load plugins from various sources.
"""

import importlib
import importlib.util
import inspect
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Type, Union
import logging

from .base import Plugin, PluginInfo, PluginType, registry

logger = logging.getLogger(__name__)


class PluginLoader:
    """Loads plugins from various sources."""
    
    def __init__(self, plugin_dirs: Optional[List[Union[str, Path]]] = None):
        """
        Initialize plugin loader.
        
        Args:
            plugin_dirs: List of directories to search for plugins
        """
        self.plugin_dirs = []
        
        # Add default plugin directories
        self._add_default_dirs()
        
        # Add user-specified directories
        if plugin_dirs:
            for dir_path in plugin_dirs:
                self.add_plugin_dir(dir_path)
    
    def _add_default_dirs(self):
        """Add default plugin directories."""
        # Built-in plugins directory
        builtin_dir = Path(__file__).parent / "builtin"
        if builtin_dir.exists():
            self.plugin_dirs.append(builtin_dir)
        
        # User plugins directory in home
        user_plugin_dir = Path.home() / ".pg-idempotent" / "plugins"
        if user_plugin_dir.exists():
            self.plugin_dirs.append(user_plugin_dir)
        
        # Current directory plugins
        cwd_plugin_dir = Path.cwd() / "pg_idempotent_plugins"
        if cwd_plugin_dir.exists():
            self.plugin_dirs.append(cwd_plugin_dir)
    
    def add_plugin_dir(self, path: Union[str, Path]):
        """Add a directory to search for plugins."""
        plugin_dir = Path(path)
        if plugin_dir.exists() and plugin_dir.is_dir():
            if plugin_dir not in self.plugin_dirs:
                self.plugin_dirs.append(plugin_dir)
                logger.info(f"Added plugin directory: {plugin_dir}")
        else:
            logger.warning(f"Plugin directory does not exist: {plugin_dir}")
    
    def load_all_plugins(self):
        """Load all plugins from configured directories."""
        loaded_count = 0
        
        for plugin_dir in self.plugin_dirs:
            count = self._load_plugins_from_dir(plugin_dir)
            loaded_count += count
        
        logger.info(f"Loaded {loaded_count} plugins total")
        return loaded_count
    
    def _load_plugins_from_dir(self, plugin_dir: Path) -> int:
        """Load plugins from a specific directory."""
        loaded_count = 0
        
        logger.info(f"Searching for plugins in: {plugin_dir}")
        
        # Look for Python files
        for file_path in plugin_dir.glob("*.py"):
            if file_path.name.startswith("_"):
                continue
            
            try:
                if self._load_plugin_from_file(file_path):
                    loaded_count += 1
            except Exception as e:
                logger.error(f"Failed to load plugin from {file_path}: {e}")
        
        # Look for Python packages
        for dir_path in plugin_dir.iterdir():
            if dir_path.is_dir() and not dir_path.name.startswith("_"):
                init_file = dir_path / "__init__.py"
                if init_file.exists():
                    try:
                        if self._load_plugin_from_package(dir_path):
                            loaded_count += 1
                    except Exception as e:
                        logger.error(f"Failed to load plugin package {dir_path}: {e}")
        
        return loaded_count
    
    def _load_plugin_from_file(self, file_path: Path) -> bool:
        """Load a plugin from a Python file."""
        module_name = f"pg_idempotent_plugin_{file_path.stem}"
        
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if not spec or not spec.loader:
            return False
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        return self._register_plugins_from_module(module)
    
    def _load_plugin_from_package(self, package_path: Path) -> bool:
        """Load a plugin from a Python package."""
        # Add parent directory to sys.path temporarily
        parent_dir = str(package_path.parent)
        sys_path_added = False
        
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
            sys_path_added = True
        
        try:
            module_name = package_path.name
            module = importlib.import_module(module_name)
            return self._register_plugins_from_module(module)
        finally:
            if sys_path_added:
                sys.path.remove(parent_dir)
    
    def _register_plugins_from_module(self, module) -> bool:
        """Register all plugin classes found in a module."""
        registered_any = False
        
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                issubclass(obj, Plugin) and 
                obj is not Plugin and
                not inspect.isabstract(obj)):
                
                try:
                    # Instantiate and register plugin
                    plugin_instance = obj()
                    registry.register(plugin_instance)
                    logger.info(f"Registered plugin: {plugin_instance.info.name}")
                    registered_any = True
                except Exception as e:
                    logger.error(f"Failed to register plugin {name}: {e}")
        
        return registered_any
    
    def load_plugin(self, name: str, path: Optional[Union[str, Path]] = None) -> bool:
        """
        Load a specific plugin by name.
        
        Args:
            name: Plugin name or module name
            path: Optional path to plugin file/directory
        
        Returns:
            True if plugin was loaded successfully
        """
        if path:
            plugin_path = Path(path)
            if plugin_path.is_file():
                return self._load_plugin_from_file(plugin_path)
            elif plugin_path.is_dir():
                return self._load_plugin_from_package(plugin_path)
        else:
            # Try to import as installed package
            try:
                module = importlib.import_module(name)
                return self._register_plugins_from_module(module)
            except ImportError:
                # Search in plugin directories
                for plugin_dir in self.plugin_dirs:
                    file_path = plugin_dir / f"{name}.py"
                    if file_path.exists():
                        return self._load_plugin_from_file(file_path)
                    
                    package_path = plugin_dir / name
                    if package_path.is_dir() and (package_path / "__init__.py").exists():
                        return self._load_plugin_from_package(package_path)
        
        logger.error(f"Plugin '{name}' not found")
        return False
    
    def reload_plugin(self, name: str) -> bool:
        """Reload a plugin by name."""
        # First unregister the plugin
        try:
            registry.unregister(name)
        except ValueError:
            logger.warning(f"Plugin '{name}' not currently loaded")
        
        # Find and reload the plugin
        plugin = registry.get_plugin(name)
        if plugin:
            # Get module from plugin class
            module = sys.modules.get(plugin.__class__.__module__)
            if module:
                importlib.reload(module)
                return self._register_plugins_from_module(module)
        
        # Try loading as new plugin
        return self.load_plugin(name)
    
    @staticmethod
    def discover_entry_point_plugins():
        """Discover plugins installed via setuptools entry points."""
        try:
            from importlib.metadata import entry_points
        except ImportError:
            try:
                from importlib_metadata import entry_points
            except ImportError:
                logger.warning("Cannot discover entry point plugins without importlib_metadata")
                return 0
        
        loaded_count = 0
        
        # Look for pg_idempotent.plugins entry points
        eps = entry_points()
        if hasattr(eps, 'select'):
            # Python 3.10+
            plugin_eps = eps.select(group='pg_idempotent.plugins')
        else:
            # Python 3.9 and below
            plugin_eps = eps.get('pg_idempotent.plugins', [])
        
        for ep in plugin_eps:
            try:
                plugin_class = ep.load()
                if inspect.isclass(plugin_class) and issubclass(plugin_class, Plugin):
                    plugin_instance = plugin_class()
                    registry.register(plugin_instance)
                    logger.info(f"Loaded entry point plugin: {plugin_instance.info.name}")
                    loaded_count += 1
            except Exception as e:
                logger.error(f"Failed to load entry point plugin {ep.name}: {e}")
        
        return loaded_count


# Convenience functions
def load_plugins(plugin_dirs: Optional[List[Union[str, Path]]] = None) -> int:
    """Load all plugins from configured directories."""
    loader = PluginLoader(plugin_dirs)
    count = loader.load_all_plugins()
    
    # Also discover entry point plugins
    count += PluginLoader.discover_entry_point_plugins()
    
    # Initialize all loaded plugins
    registry.initialize_all()
    
    return count


def load_plugin(name: str, path: Optional[Union[str, Path]] = None) -> bool:
    """Load a specific plugin."""
    loader = PluginLoader()
    success = loader.load_plugin(name, path)
    
    if success:
        plugin = registry.get_plugin(name)
        if plugin:
            plugin.initialize()
    
    return success


def reload_plugin(name: str) -> bool:
    """Reload a plugin."""
    loader = PluginLoader()
    success = loader.reload_plugin(name)
    
    if success:
        plugin = registry.get_plugin(name)
        if plugin:
            plugin.initialize()
    
    return success


def get_loaded_plugins() -> Dict[str, PluginInfo]:
    """Get information about all loaded plugins."""
    plugins = {}
    for plugin in registry.get_all_plugins():
        plugins[plugin.info.name] = plugin.info
    return plugins


def get_plugins_by_type(plugin_type: PluginType) -> List[Plugin]:
    """Get all plugins of a specific type."""
    return registry.get_plugins_by_type(plugin_type)