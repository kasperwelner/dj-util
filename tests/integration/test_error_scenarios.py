"""Integration tests for error scenarios."""
import pytest
from unittest.mock import patch
from src.cli.export_command import export_command


class TestErrorScenarios:
    """Test error handling in various failure scenarios."""
    
    def test_database_not_found_error(self):
        """Test graceful handling when database is not found."""
        with patch('src.services.rekordbox.RekordboxAdapter') as mock_adapter:
            mock_adapter.return_value.connect.return_value = False
            mock_adapter.return_value.error_message = "Database not found"
            
            with pytest.raises(SystemExit) as exc_info:
                export_command("output.csv")
            
            assert exc_info.value.code == 2
    
    def test_no_tags_selected_error(self):
        """Test error when user doesn't select any tags."""
        with patch('src.services.tag_selector.TagSelector') as mock_selector:
            mock_selector.return_value.get_user_selection.return_value = []
            
            with pytest.raises(ValueError, match="At least one tag must be selected"):
                export_command("output.csv")
    
    def test_no_matching_tracks_warning(self):
        """Test warning when no streaming tracks match selected tags."""
        with patch('src.services.rekordbox.RekordboxAdapter') as mock_adapter:
            mock_adapter.return_value.get_streaming_tracks_by_tags.return_value = []
            
            with patch('click.echo') as mock_echo:
                with pytest.raises(SystemExit) as exc_info:
                    export_command("output.csv")
                
                mock_echo.assert_called_with("Warning: No streaming tracks match selected tags")
                assert exc_info.value.code == 4
    
    def test_output_directory_not_writable(self):
        """Test error when output directory is not writable."""
        with patch('os.access', return_value=False):
            with pytest.raises(ValueError, match="Output directory is not writable"):
                export_command("/readonly/output.csv")
    
    def test_database_locked_by_rekordbox(self):
        """Test handling when database is locked by Rekordbox."""
        with patch('src.services.rekordbox.RekordboxAdapter') as mock_adapter:
            mock_adapter.return_value.connect.side_effect = PermissionError("Database locked")
            
            with pytest.raises(SystemExit) as exc_info:
                export_command("output.csv")
            
            assert exc_info.value.code == 2