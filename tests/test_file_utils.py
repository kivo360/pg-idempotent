"""Comprehensive tests for file utilities."""

import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

from pg_idempotent.utils.file_utils import FileOperations


class TestFileOperations:
    """Test cases for FileOperations class."""
    
    def test_backup_file_basic(self):
        """Test basic file backup functionality."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
            f.write("CREATE TABLE test (id int);")
            original_path = Path(f.name)
        
        try:
            # Create backup
            backup_path = FileOperations.backup_file(original_path)
            
            # Verify backup exists
            assert backup_path.exists()
            assert backup_path.parent.name == ".pg-idempotent-backups"
            assert backup_path.suffix == ".sql"
            assert original_path.stem in backup_path.stem
            
            # Verify content is same
            assert backup_path.read_text() == original_path.read_text()
            
        finally:
            # Cleanup
            original_path.unlink(missing_ok=True)
            if backup_path.exists():
                backup_path.unlink()
            if backup_path.parent.exists():
                shutil.rmtree(backup_path.parent)
    
    def test_backup_file_custom_directory(self):
        """Test file backup with custom backup directory."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
            f.write("CREATE TABLE test (id int);")
            original_path = Path(f.name)
        
        with tempfile.TemporaryDirectory() as backup_dir:
            # Create backup
            backup_path = FileOperations.backup_file(original_path, backup_dir)
            
            # Verify backup exists in custom directory
            assert backup_path.exists()
            assert backup_path.parent == Path(backup_dir)
            assert backup_path.read_text() == original_path.read_text()
        
        # Cleanup
        original_path.unlink(missing_ok=True)
    
    def test_backup_file_timestamp(self):
        """Test that backup files have timestamp in name."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
            f.write("CREATE TABLE test (id int);")
            original_path = Path(f.name)
        
        try:
            # Create backup
            backup_path = FileOperations.backup_file(original_path)
            
            # Check timestamp format in filename
            timestamp_part = backup_path.stem.split('_')[-2:]
            timestamp_str = '_'.join(timestamp_part)
            
            # Try to parse timestamp
            datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            
        finally:
            # Cleanup
            original_path.unlink(missing_ok=True)
            if backup_path.exists():
                backup_path.unlink()
            if backup_path.parent.exists():
                shutil.rmtree(backup_path.parent)
    
    def test_backup_nonexistent_file(self):
        """Test backup of non-existent file."""
        non_existent = Path("/tmp/nonexistent_file.sql")
        
        with pytest.raises(FileNotFoundError) as exc_info:
            FileOperations.backup_file(non_existent)
        
        assert "File not found" in str(exc_info.value)
    
    def test_find_sql_files_basic(self):
        """Test finding SQL files in a directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create SQL files
            (temp_path / "file1.sql").write_text("SELECT 1;")
            (temp_path / "file2.sql").write_text("SELECT 2;")
            (temp_path / "file3.txt").write_text("Not SQL")
            
            # Find SQL files
            sql_files = FileOperations.find_sql_files(temp_path, recursive=False)
            
            assert len(sql_files) == 2
            assert all(f.suffix == ".sql" for f in sql_files)
            assert Path(temp_path / "file1.sql") in sql_files
            assert Path(temp_path / "file2.sql") in sql_files
    
    def test_find_sql_files_recursive(self):
        """Test finding SQL files recursively."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create nested structure
            (temp_path / "file1.sql").write_text("SELECT 1;")
            subdir1 = temp_path / "subdir1"
            subdir1.mkdir()
            (subdir1 / "file2.sql").write_text("SELECT 2;")
            subdir2 = subdir1 / "subdir2"
            subdir2.mkdir()
            (subdir2 / "file3.sql").write_text("SELECT 3;")
            
            # Find SQL files recursively
            sql_files = FileOperations.find_sql_files(temp_path, recursive=True)
            
            assert len(sql_files) == 3
            # Check files are sorted
            file_names = [f.name for f in sql_files]
            assert file_names == sorted(file_names)
    
    def test_find_sql_files_nonexistent_directory(self):
        """Test finding SQL files in non-existent directory."""
        non_existent = Path("/tmp/nonexistent_directory")
        
        with pytest.raises(FileNotFoundError) as exc_info:
            FileOperations.find_sql_files(non_existent)
        
        assert "Directory not found" in str(exc_info.value)
    
    def test_find_sql_files_empty_directory(self):
        """Test finding SQL files in empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            sql_files = FileOperations.find_sql_files(temp_dir)
            assert len(sql_files) == 0
    
    def test_ensure_parent_dir_basic(self):
        """Test ensuring parent directory exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            file_path = temp_path / "subdir1" / "subdir2" / "file.sql"
            
            # Ensure parent directory
            FileOperations.ensure_parent_dir(file_path)
            
            assert file_path.parent.exists()
            assert file_path.parent.is_dir()
    
    def test_ensure_parent_dir_already_exists(self):
        """Test ensuring parent directory when it already exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            file_path = temp_path / "file.sql"
            
            # Parent already exists
            FileOperations.ensure_parent_dir(file_path)
            
            # Should not raise error
            assert temp_path.exists()
    
    def test_get_relative_path_basic(self):
        """Test getting relative path."""
        base = Path("/home/user/project")
        file_path = Path("/home/user/project/src/file.sql")
        
        relative = FileOperations.get_relative_path(file_path, base)
        
        assert relative == Path("src/file.sql")
    
    def test_get_relative_path_not_subpath(self):
        """Test getting relative path when file is not under base."""
        base = Path("/home/user/project1")
        file_path = Path("/home/user/project2/file.sql")
        
        relative = FileOperations.get_relative_path(file_path, base)
        
        # Should return original path when not a subpath
        assert relative == file_path.resolve()
    
    def test_get_relative_path_with_symlinks(self):
        """Test getting relative path with symbolic links."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create actual directory and file
            actual_dir = temp_path / "actual"
            actual_dir.mkdir()
            actual_file = actual_dir / "file.sql"
            actual_file.write_text("SELECT 1;")
            
            # Create symlink
            link_dir = temp_path / "link"
            link_dir.symlink_to(actual_dir)
            
            # Get relative path through symlink
            relative = FileOperations.get_relative_path(
                link_dir / "file.sql",
                temp_path
            )
            
            # Should resolve symlinks
            assert "actual" in str(relative)
    
    def test_is_supabase_migration_by_path(self):
        """Test detecting Supabase migration by path."""
        # Test paths that should be migrations
        migration_paths = [
            Path("supabase/migrations/20231225_create_users.sql"),
            Path("project/supabase/migrations/file.sql"),
            Path("./supabase/migrations/test.sql"),
        ]
        
        for path in migration_paths:
            assert FileOperations.is_supabase_migration(path) is True
        
        # Test paths that shouldn't be migrations
        non_migration_paths = [
            Path("migrations/file.sql"),
            Path("supabase/file.sql"),
            Path("other/directory/file.sql"),
        ]
        
        for path in non_migration_paths:
            assert FileOperations.is_supabase_migration(path) is False
    
    def test_is_supabase_migration_by_filename(self):
        """Test detecting Supabase migration by filename pattern."""
        # Test filenames that match pattern (14 digits + name)
        migration_files = [
            Path("20231225120000_create_users.sql"),
            Path("20240101000000_add_indexes.sql"),
            Path("19990101000000_init.sql"),
        ]
        
        for path in migration_files:
            assert FileOperations.is_supabase_migration(path) is True
        
        # Test filenames that don't match pattern
        non_migration_files = [
            Path("create_users.sql"),
            Path("2023_create_users.sql"),  # Not enough digits
            Path("20231225120000.sql"),  # No underscore
            Path("20231225120000_create_users.txt"),  # Wrong extension
        ]
        
        for path in non_migration_files:
            assert FileOperations.is_supabase_migration(path) is False
    
    def test_file_operations_with_pathlib_strings(self):
        """Test that file operations work with both Path objects and strings."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
            f.write("CREATE TABLE test (id int);")
            file_path = f.name
        
        try:
            # Test with string path
            backup_path = FileOperations.backup_file(file_path)
            assert backup_path.exists()
            
            # Cleanup
            backup_path.unlink()
            if backup_path.parent.exists():
                shutil.rmtree(backup_path.parent)
            
        finally:
            Path(file_path).unlink(missing_ok=True)
    
    def test_backup_file_preserves_metadata(self):
        """Test that backup preserves file metadata."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
            f.write("CREATE TABLE test (id int);")
            original_path = Path(f.name)
        
        try:
            # Get original stats
            original_stat = original_path.stat()
            
            # Create backup
            backup_path = FileOperations.backup_file(original_path)
            backup_stat = backup_path.stat()
            
            # Check that size is preserved
            assert backup_stat.st_size == original_stat.st_size
            
            # Check that mode is preserved (at least read/write bits)
            assert backup_stat.st_mode == original_stat.st_mode
            
        finally:
            # Cleanup
            original_path.unlink(missing_ok=True)
            if backup_path.exists():
                backup_path.unlink()
            if backup_path.parent.exists():
                shutil.rmtree(backup_path.parent)
    
    def test_find_sql_files_case_sensitivity(self):
        """Test that find_sql_files is case sensitive for extensions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create files with different cases
            (temp_path / "file1.sql").write_text("SELECT 1;")
            (temp_path / "file2.SQL").write_text("SELECT 2;")
            (temp_path / "file3.Sql").write_text("SELECT 3;")
            
            # Find SQL files (should only match lowercase .sql)
            sql_files = FileOperations.find_sql_files(temp_path)
            
            # On case-sensitive systems, should only find .sql
            # On case-insensitive systems (like macOS), might find all
            assert len(sql_files) >= 1
            assert any(f.name == "file1.sql" for f in sql_files)
    
    @patch('pathlib.Path.mkdir')
    def test_ensure_parent_dir_error_handling(self, mock_mkdir):
        """Test error handling in ensure_parent_dir."""
        mock_mkdir.side_effect = PermissionError("Permission denied")
        
        # Should propagate the error
        with pytest.raises(PermissionError):
            FileOperations.ensure_parent_dir("/restricted/path/file.sql")
    
    def test_complex_backup_scenario(self):
        """Test complex backup scenario with multiple backups."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
            f.write("CREATE TABLE test (id int);")
            original_path = Path(f.name)
        
        backup_paths = []
        try:
            # Create multiple backups
            for i in range(3):
                backup_path = FileOperations.backup_file(original_path)
                backup_paths.append(backup_path)
                # Delay 1 second to ensure different timestamps (timestamp format is YYYYMMDD_HHMMSS)
                import time
                time.sleep(1.1)
            
            # Verify all backups exist and have unique names
            assert len(set(backup_paths)) == 3
            for backup in backup_paths:
                assert backup.exists()
                assert backup.read_text() == original_path.read_text()
            
        finally:
            # Cleanup
            original_path.unlink(missing_ok=True)
            for backup in backup_paths:
                if backup.exists():
                    backup.unlink()
            if backup_paths and backup_paths[0].parent.exists():
                shutil.rmtree(backup_paths[0].parent)