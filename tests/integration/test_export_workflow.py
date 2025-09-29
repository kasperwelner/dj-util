"""Integration tests for complete export workflow."""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.cli.export_command import export_command


class TestExportWorkflow:
    """Test the complete export workflow from database to CSV."""
    
    def test_complete_workflow_from_db_to_csv(self, tmp_path):
        """Test full workflow: connect -> select tags -> filter -> export."""
        output_file = tmp_path / "export.csv"
        
        with patch('src.services.rekordbox.RekordboxAdapter') as mock_adapter:
            with patch('src.services.tag_selector.TagSelector') as mock_selector:
                with patch('src.services.csv_exporter.CSVExporter') as mock_exporter:
                    # Setup mocks
                    mock_adapter.return_value.connect.return_value = True
                    mock_adapter.return_value.get_all_mytags.return_value = [
                        Mock(id=1, name="Tag1")
                    ]
                    mock_selector.return_value.get_user_selection.return_value = [1]
                    mock_adapter.return_value.get_streaming_tracks_by_tags.return_value = [
                        Mock(id=1, artist="Artist", title="Title")
                    ]
                    
                    # Run workflow
                    result = export_command(str(output_file))
                    
                    assert result == 0
                    mock_exporter.return_value.export.assert_called_once()
    
    def test_workflow_handles_no_matching_tracks(self):
        """Test workflow when no tracks match selected tags."""
        with patch('src.services.rekordbox.RekordboxAdapter') as mock_adapter:
            mock_adapter.return_value.get_streaming_tracks_by_tags.return_value = []
            
            with patch('click.echo') as mock_echo:
                result = export_command("output.csv")
                mock_echo.assert_called_with("Warning: No streaming tracks match selected tags")
    
    def test_workflow_with_progress_feedback(self):
        """Test that progress feedback is shown during export."""
        with patch('src.lib.progress.show_progress') as mock_progress:
            with patch('src.services.rekordbox.RekordboxAdapter'):
                export_command("output.csv", verbose=True)
                assert mock_progress.called