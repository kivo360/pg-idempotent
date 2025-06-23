"""Comprehensive tests for PG Idempotent CLI."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from pg_idempotent.cli import app

runner = CliRunner()


@pytest.fixture
def temp_sql_file():
    """Create a temporary SQL file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False) as f:
        f.write("""
        CREATE TABLE users (id serial PRIMARY KEY);
        CREATE INDEX idx_users ON users(id);
        """)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    temp_path.unlink(missing_ok=True)
    # Also cleanup backup if created
    backup_path = temp_path.with_suffix(".sql.backup")
    backup_path.unlink(missing_ok=True)


@pytest.fixture
def temp_dir_with_sql_files():
    """Create a temporary directory with SQL files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create some SQL files
        (temp_path / "file1.sql").write_text("CREATE TABLE test1 (id int);")
        (temp_path / "file2.sql").write_text("CREATE TABLE test2 (id int);")

        # Create subdirectory with more files
        subdir = temp_path / "subdir"
        subdir.mkdir()
        (subdir / "file3.sql").write_text("CREATE TABLE test3 (id int);")

        yield temp_path


class TestTransformCommand:
    """Test cases for the transform command."""

    def test_transform_basic(self, temp_sql_file):
        """Test basic transformation of SQL file."""
        result = runner.invoke(app, ["transform", str(temp_sql_file)])

        assert result.exit_code == 0
        assert "Transformation completed" in result.stdout
        assert "Processed 2 statements" in result.stdout

    def test_transform_with_output_file(self, temp_sql_file):
        """Test transformation with specified output file."""
        with tempfile.NamedTemporaryFile(suffix=".sql", delete=False) as out_file:
            output_path = Path(out_file.name)

        result = runner.invoke(app, ["transform", str(temp_sql_file), "--output", str(output_path)])

        assert result.exit_code == 0
        assert output_path.exists()
        assert output_path.stat().st_size > 0

        # Cleanup
        output_path.unlink()

    def test_transform_no_backup(self, temp_sql_file):
        """Test transformation without creating backup."""
        result = runner.invoke(app, ["transform", str(temp_sql_file), "--no-backup"])

        assert result.exit_code == 0
        backup_path = temp_sql_file.with_suffix(".sql.backup")
        assert not backup_path.exists()

    def test_transform_with_stats(self, temp_sql_file):
        """Test transformation with statistics display."""
        result = runner.invoke(app, ["transform", str(temp_sql_file), "--stats"])

        assert result.exit_code == 0
        assert "Transformation Statistics" in result.stdout
        assert "Total Statements" in result.stdout

    def test_transform_with_validation(self, temp_sql_file):
        """Test transformation with validation."""
        result = runner.invoke(app, ["transform", str(temp_sql_file), "--validate"])

        assert result.exit_code == 0
        assert "Validation passed" in result.stdout or "Validation issues" in result.stdout

    def test_transform_nonexistent_file(self):
        """Test transformation of non-existent file."""
        result = runner.invoke(app, ["transform", "nonexistent.sql"])

        assert result.exit_code == 1
        assert "File not found" in result.stdout

    @patch("pg_idempotent.cli.SQLTransformer")
    def test_transform_with_errors(self, mock_transformer, temp_sql_file):
        """Test handling of transformation errors."""
        # Mock transformer to return error
        mock_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.errors = ["Test error 1", "Test error 2"]
        mock_instance.transform_file.return_value = mock_result
        mock_transformer.return_value = mock_instance

        result = runner.invoke(app, ["transform", str(temp_sql_file)])

        assert result.exit_code == 1
        assert "Transformation failed" in result.stdout
        assert "Test error 1" in result.stdout

    @patch("pg_idempotent.cli.SQLTransformer")
    def test_transform_with_warnings(self, mock_transformer, temp_sql_file):
        """Test handling of transformation warnings."""
        # Mock transformer to return warnings
        mock_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.statement_count = 2
        mock_result.transformed_count = 1
        mock_result.warnings = ["Test warning 1"]
        mock_result.errors = []
        mock_result.transformed_sql = "-- Transformed SQL"
        mock_instance.transform_file.return_value = mock_result
        mock_instance.validate_transformed_sql.return_value = {"valid": True, "issues": []}
        mock_transformer.return_value = mock_instance

        result = runner.invoke(app, ["transform", str(temp_sql_file)])

        assert result.exit_code == 0
        assert "Warnings:" in result.stdout
        assert "Test warning 1" in result.stdout


class TestCheckCommand:
    """Test cases for the check command."""

    def test_check_basic(self, temp_sql_file):
        """Test basic file analysis."""
        result = runner.invoke(app, ["check", str(temp_sql_file)])

        assert result.exit_code == 0
        assert "Transformation Statistics" in result.stdout
        assert "Statement Details" in result.stdout

    def test_check_nonexistent_file(self):
        """Test checking non-existent file."""
        result = runner.invoke(app, ["check", "nonexistent.sql"])

        assert result.exit_code == 1
        assert "File not found" in result.stdout

    def test_check_shows_statement_types(self, temp_sql_file):
        """Test that check command shows statement types."""
        result = runner.invoke(app, ["check", str(temp_sql_file)])

        assert result.exit_code == 0
        assert "CREATE_TABLE" in result.stdout
        assert "CREATE_INDEX" in result.stdout

    @patch("pg_idempotent.cli.SQLTransformer")
    def test_check_with_many_statements(self, mock_transformer, temp_sql_file):
        """Test check command with more than 10 statements."""
        # Create mock statements
        mock_statements = []
        for i in range(15):
            stmt = MagicMock()
            stmt.statement_type = f"TYPE_{i}"
            stmt.object_name = f"object_{i}"
            stmt.is_idempotent = False
            stmt.can_be_wrapped = True
            stmt.error = None
            mock_statements.append(stmt)

        mock_instance = MagicMock()
        mock_instance.get_transformation_stats.return_value = {
            "total_statements": 15,
            "already_idempotent": 0,
            "transformable": 15,
            "not_transformable": 0,
            "errors": 0,
            "by_type": {},
        }
        mock_instance.parser.parse_sql.return_value = mock_statements
        mock_transformer.return_value = mock_instance

        result = runner.invoke(app, ["check", str(temp_sql_file)])

        assert result.exit_code == 0
        assert "and 5 more statements" in result.stdout


class TestPreviewCommand:
    """Test cases for the preview command."""

    def test_preview_basic(self, temp_sql_file):
        """Test basic preview functionality."""
        result = runner.invoke(app, ["preview", str(temp_sql_file)])

        assert result.exit_code == 0
        assert "Preview:" in result.stdout
        assert temp_sql_file.name in result.stdout

    def test_preview_with_lines(self, temp_sql_file):
        """Test preview with custom line count."""
        result = runner.invoke(app, ["preview", str(temp_sql_file), "--lines", "5"])

        assert result.exit_code == 0
        assert "Showing first" in result.stdout

    def test_preview_nonexistent_file(self):
        """Test preview of non-existent file."""
        result = runner.invoke(app, ["preview", "nonexistent.sql"])

        assert result.exit_code == 1
        assert "File not found" in result.stdout

    @patch("pg_idempotent.cli.SQLTransformer")
    def test_preview_transformation_error(self, mock_transformer, temp_sql_file):
        """Test preview when transformation fails."""
        mock_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.errors = ["Transformation error"]
        mock_instance.transform_file.return_value = mock_result
        mock_transformer.return_value = mock_instance

        result = runner.invoke(app, ["preview", str(temp_sql_file)])

        assert result.exit_code == 1
        assert "Transformation failed" in result.stdout


class TestBatchCommand:
    """Test cases for the batch command."""

    def test_batch_basic(self, temp_dir_with_sql_files):
        """Test basic batch processing."""
        result = runner.invoke(app, ["batch", str(temp_dir_with_sql_files)])

        assert result.exit_code == 0
        assert "Found 2 files to process" in result.stdout
        assert "Summary:" in result.stdout
        assert "2 files processed successfully" in result.stdout

    def test_batch_recursive(self, temp_dir_with_sql_files):
        """Test recursive batch processing."""
        result = runner.invoke(app, ["batch", str(temp_dir_with_sql_files), "--recursive"])

        assert result.exit_code == 0
        assert "Found 3 files to process" in result.stdout

    def test_batch_with_pattern(self, temp_dir_with_sql_files):
        """Test batch processing with file pattern."""
        # Create a non-SQL file
        (temp_dir_with_sql_files / "file.txt").write_text("Not SQL")

        result = runner.invoke(
            app, ["batch", str(temp_dir_with_sql_files), "--pattern", "file1.sql"]
        )

        assert result.exit_code == 0
        assert "Found 1 files to process" in result.stdout

    def test_batch_with_output_dir(self, temp_dir_with_sql_files):
        """Test batch processing with output directory."""
        with tempfile.TemporaryDirectory() as out_dir:
            result = runner.invoke(
                app, ["batch", str(temp_dir_with_sql_files), "--output-dir", out_dir]
            )

            assert result.exit_code == 0

            # Check output files were created
            output_path = Path(out_dir)
            assert (output_path / "file1.sql").exists()
            assert (output_path / "file2.sql").exists()

    def test_batch_with_output_dir_recursive(self, temp_dir_with_sql_files):
        """Test recursive batch processing with output directory."""
        with tempfile.TemporaryDirectory() as out_dir:
            result = runner.invoke(
                app, ["batch", str(temp_dir_with_sql_files), "--output-dir", out_dir, "--recursive"]
            )

            assert result.exit_code == 0

            # Check output files with preserved structure
            output_path = Path(out_dir)
            assert (output_path / "file1.sql").exists()
            assert (output_path / "subdir" / "file3.sql").exists()

    def test_batch_no_files_found(self):
        """Test batch processing when no files match."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(app, ["batch", temp_dir, "--pattern", "*.txt"])

            assert result.exit_code == 0
            assert "No files found" in result.stdout

    def test_batch_nonexistent_directory(self):
        """Test batch processing with non-existent directory."""
        result = runner.invoke(app, ["batch", "/nonexistent/directory"])

        assert result.exit_code == 1
        assert "Directory not found" in result.stdout

    @patch("pg_idempotent.cli.SQLTransformer")
    def test_batch_with_errors(self, mock_transformer, temp_dir_with_sql_files):
        """Test batch processing with transformation errors."""
        # Mock transformer to fail on first file, succeed on second
        mock_instance = MagicMock()

        fail_result = MagicMock()
        fail_result.success = False
        fail_result.errors = ["Failed to transform"]

        success_result = MagicMock()
        success_result.success = True
        success_result.statement_count = 1
        success_result.transformed_count = 1

        mock_instance.transform_file.side_effect = [fail_result, success_result]
        mock_transformer.return_value = mock_instance

        result = runner.invoke(app, ["batch", str(temp_dir_with_sql_files)])

        assert result.exit_code == 0
        assert "1 files processed successfully" in result.stdout
        assert "1 files failed" in result.stdout


class TestCLIIntegration:
    """Integration tests for CLI commands."""

    def test_transform_then_check(self, temp_sql_file):
        """Test transforming a file then checking it."""
        # First transform
        result1 = runner.invoke(app, ["transform", str(temp_sql_file)])
        assert result1.exit_code == 0

        # Then check the transformed file
        result2 = runner.invoke(app, ["check", str(temp_sql_file)])
        assert result2.exit_code == 0

    def test_dry_run_workflow(self, temp_sql_file):
        """Test a dry-run workflow: check, preview, then transform."""
        # Check what needs transformation
        result1 = runner.invoke(app, ["check", str(temp_sql_file)])
        assert result1.exit_code == 0

        # Preview the transformation
        result2 = runner.invoke(app, ["preview", str(temp_sql_file)])
        assert result2.exit_code == 0

        # Actually transform with validation
        result3 = runner.invoke(app, ["transform", str(temp_sql_file), "--validate"])
        assert result3.exit_code == 0

    def test_batch_then_check_individual(self, temp_dir_with_sql_files):
        """Test batch processing then checking individual files."""
        # Batch process
        result1 = runner.invoke(app, ["batch", str(temp_dir_with_sql_files)])
        assert result1.exit_code == 0

        # Check one of the processed files
        file_path = temp_dir_with_sql_files / "file1.sql"
        result2 = runner.invoke(app, ["check", str(file_path)])
        assert result2.exit_code == 0


class TestCLIErrorHandling:
    """Test error handling in CLI."""

    def test_invalid_command(self):
        """Test handling of invalid commands."""
        result = runner.invoke(app, ["invalid-command"])
        assert result.exit_code != 0

    def test_missing_required_arguments(self):
        """Test handling of missing required arguments."""
        result = runner.invoke(app, ["transform"])
        assert result.exit_code != 0
        # Typer puts error messages in stderr or sometimes in stdout
        output = result.stdout + result.stderr if hasattr(result, "stderr") else result.stdout
        assert (
            "Missing" in output or "Error" in output or result.exit_code == 2
        )  # exit code 2 is for missing args

    def test_invalid_option_values(self, temp_sql_file):
        """Test handling of invalid option values."""
        result = runner.invoke(app, ["preview", str(temp_sql_file), "--lines", "not-a-number"])
        assert result.exit_code != 0
