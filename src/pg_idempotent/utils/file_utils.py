"""File system utilities for the transformer."""
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Union, List


class FileOperations:
    """Handles file system operations with backup support."""
    
    @staticmethod
    def backup_file(file_path: Union[str, Path], backup_dir: Optional[Union[str, Path]] = None) -> Path:
        """Create a backup of a file."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine backup directory
        if backup_dir:
            backup_path = Path(backup_dir)
        else:
            backup_path = file_path.parent / ".pg-idempotent-backups"
        
        # Create backup directory
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_path / f"{file_path.stem}_{timestamp}{file_path.suffix}"
        
        # Copy file
        shutil.copy2(file_path, backup_file)
        
        return backup_file
    
    @staticmethod
    def find_sql_files(directory: Union[str, Path], recursive: bool = True) -> List[Path]:
        """Find all SQL files in a directory."""
        directory = Path(directory)
        
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        if recursive:
            return sorted(directory.glob("**/*.sql"))
        else:
            return sorted(directory.glob("*.sql"))
    
    @staticmethod
    def ensure_parent_dir(file_path: Union[str, Path]) -> None:
        """Ensure parent directory exists for a file."""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def get_relative_path(file_path: Union[str, Path], base_path: Union[str, Path]) -> Path:
        """Get relative path from base path."""
        file_path = Path(file_path).resolve()
        base_path = Path(base_path).resolve()
        
        try:
            return file_path.relative_to(base_path)
        except ValueError:
            # Not a subpath, return original
            return file_path
    
    @staticmethod
    def is_supabase_migration(file_path: Union[str, Path]) -> bool:
        """Check if file is a Supabase migration."""
        file_path = Path(file_path)
        
        # Check if in supabase/migrations directory
        parts = file_path.parts
        if "supabase" in parts and "migrations" in parts:
            return True
        
        # Check filename pattern (timestamp_name.sql)
        import re
        pattern = r'^\d{14}_.*\.sql$'
        return bool(re.match(pattern, file_path.name))