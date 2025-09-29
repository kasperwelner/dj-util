"""CLI tests for rekordbox-export command."""
import pytest
from click.testing import CliRunner
from unittest.mock import patch, Mock
from src.cli.export_command import cli


class TestExportCommand:
    """Test the CLI command interface."""
    
    def test_default_output_filename(self):
        """Test command uses default output filename."""
        runner = CliRunner()
        
        with patch('src.cli.export_command.export_command') as mock_export:
            mock_export.return_value = 0
            result = runner.invoke(cli, [])
            
            mock_export.assert_called_with('rekordbox_export.csv', 
                                          database=None, 
                                          tags=None,
                                          verbose=False,
                                          limit=None,
                                          overwrite=False)
    
    def test_custom_output_filename(self):
        """Test command accepts custom output filename."""
        runner = CliRunner()
        
        with patch('src.cli.export_command.export_command') as mock_export:
            mock_export.return_value = 0
            result = runner.invoke(cli, ['custom.csv'])
            
            mock_export.assert_called_with('custom.csv',
                                          database=None,
                                          tags=None,
                                          verbose=False,
                                          limit=None,
                                          overwrite=False)
    
    def test_database_option(self):
        """Test --database option for custom database path."""
        runner = CliRunner()
        
        with patch('src.cli.export_command.export_command') as mock_export:
            result = runner.invoke(cli, ['--database', '/path/to/db.db'])
            mock_export.assert_called_with('rekordbox_export.csv',
                                          database='/path/to/db.db',
                                          tags=None,
                                          verbose=False,
                                          limit=None,
                                          overwrite=False)
    
    def test_tags_option(self):
        """Test --tags option for pre-selecting tags."""
        runner = CliRunner()
        
        with patch('src.cli.export_command.export_command') as mock_export:
            result = runner.invoke(cli, ['--tags', 'House', '--tags', 'Techno'])
            mock_export.assert_called_with('rekordbox_export.csv',
                                          database=None,
                                          tags=['House', 'Techno'],
                                          verbose=False,
                                          limit=None,
                                          overwrite=False)
    
    def test_verbose_option(self):
        """Test --verbose flag enables detailed output."""
        runner = CliRunner()
        
        with patch('src.cli.export_command.export_command') as mock_export:
            result = runner.invoke(cli, ['--verbose'])
            mock_export.assert_called_with('rekordbox_export.csv',
                                          database=None,
                                          tags=None,
                                          verbose=True,
                                          limit=None,
                                          overwrite=False)
    
    def test_limit_option(self):
        """Test --limit option restricts number of exported tracks."""
        runner = CliRunner()
        
        with patch('src.cli.export_command.export_command') as mock_export:
            result = runner.invoke(cli, ['--limit', '100'])
            mock_export.assert_called_with('rekordbox_export.csv',
                                          database=None,
                                          tags=None,
                                          verbose=False,
                                          limit=100,
                                          overwrite=False)
    
    def test_overwrite_option(self):
        """Test --overwrite flag skips confirmation."""
        runner = CliRunner()
        
        with patch('src.cli.export_command.export_command') as mock_export:
            result = runner.invoke(cli, ['--overwrite', '-f'])
            mock_export.assert_called_with('rekordbox_export.csv',
                                          database=None,
                                          tags=None,
                                          verbose=False,
                                          limit=None,
                                          overwrite=True)
    
    def test_help_option(self):
        """Test --help displays usage information."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert 'Export Rekordbox streaming tracks' in result.output
        assert '--database' in result.output
        assert '--tags' in result.output