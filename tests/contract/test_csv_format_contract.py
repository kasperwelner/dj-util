"""Contract tests for CSV output format compliance."""
import pytest
import csv
import io
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from src.services.csv_exporter import CSVExporter
from src.models.track import Track


class TestCSVFormatContract:
    """Test CSV output conforms to RFC 4180 and requirements."""

    def test_csv_includes_required_columns(self, tmp_path):
        """Test CSV has ID, Artist, Title columns in correct order."""
        exporter = CSVExporter()
        output_file = tmp_path / "test.csv"
        
        tracks = [
            Track(id=1, artist="Test Artist", title="Test Title")
        ]
        
        exporter.export(tracks, str(output_file))
        
        with open(output_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            assert headers == ['ID', 'Artist', 'Title']

    def test_csv_uses_utf8_sig_encoding(self, tmp_path):
        """Test CSV file uses UTF-8 with BOM for Excel compatibility."""
        exporter = CSVExporter()
        output_file = tmp_path / "test.csv"
        
        tracks = [
            Track(id=1, artist="Artist", title="Title")
        ]
        
        exporter.export(tracks, str(output_file))
        
        # Check for UTF-8 BOM
        with open(output_file, 'rb') as f:
            bom = f.read(3)
            assert bom == b'\xef\xbb\xbf'  # UTF-8 BOM

    def test_csv_handles_unicode_characters(self, tmp_path):
        """Test CSV correctly handles Unicode characters."""
        exporter = CSVExporter()
        output_file = tmp_path / "test_unicode.csv"
        
        tracks = [
            Track(id=1, artist="日本人", title="Москва"),
            Track(id=2, artist="Björk", title="Café 🎵"),
            Track(id=3, artist="Σοφία", title="München")
        ]
        
        exporter.export(tracks, str(output_file))
        
        with open(output_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert rows[0]['Artist'] == "日本人"
            assert rows[1]['Title'] == "Café 🎵"
            assert rows[2]['Artist'] == "Σοφία"

    def test_csv_escapes_special_characters(self, tmp_path):
        """Test CSV properly escapes commas, quotes, and newlines per RFC 4180."""
        exporter = CSVExporter()
        output_file = tmp_path / "test_escaping.csv"
        
        tracks = [
            Track(id=1, artist='Artist, with comma', title='Title with "quotes"'),
            Track(id=2, artist='Artist\nwith\nnewlines', title='Title; semicolon'),
            Track(id=3, artist='Mix: "Dance"', title='Song, Part 2')
        ]
        
        exporter.export(tracks, str(output_file))
        
        with open(output_file, 'r', encoding='utf-8-sig') as f:
            content = f.read()
            # Verify quotes are escaped properly
            assert '"Artist, with comma"' in content
            assert '"Title with ""quotes"""' in content
            assert '"Artist\nwith\nnewlines"' in content

    def test_csv_handles_missing_fields(self, tmp_path):
        """Test CSV leaves fields empty when artist or title is None."""
        exporter = CSVExporter()
        output_file = tmp_path / "test_missing.csv"
        
        tracks = [
            Track(id=1, artist=None, title="Only Title"),
            Track(id=2, artist="Only Artist", title=None),
            Track(id=3, artist=None, title=None),
            Track(id=4, artist="", title="")
        ]
        
        exporter.export(tracks, str(output_file))
        
        with open(output_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert rows[0]['Artist'] == ''
            assert rows[0]['Title'] == 'Only Title'
            assert rows[1]['Artist'] == 'Only Artist'
            assert rows[1]['Title'] == ''
            assert rows[2]['Artist'] == ''
            assert rows[2]['Title'] == ''
            assert rows[3]['Artist'] == ''
            assert rows[3]['Title'] == ''

    def test_csv_includes_all_duplicate_tracks(self, tmp_path):
        """Test CSV includes all tracks even with duplicate artist/title."""
        exporter = CSVExporter()
        output_file = tmp_path / "test_duplicates.csv"
        
        tracks = [
            Track(id=100, artist="Same Artist", title="Same Title"),
            Track(id=101, artist="Same Artist", title="Same Title"),
            Track(id=102, artist="Same Artist", title="Same Title")
        ]
        
        exporter.export(tracks, str(output_file))
        
        with open(output_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 3
            assert rows[0]['ID'] == '100'
            assert rows[1]['ID'] == '101'
            assert rows[2]['ID'] == '102'
            assert all(row['Artist'] == 'Same Artist' for row in rows)

    def test_csv_validates_output_path(self):
        """Test CSV exporter validates output path before writing."""
        exporter = CSVExporter()
        
        # Test invalid directory
        with pytest.raises(ValueError, match="Output directory does not exist"):
            exporter.export([], "/nonexistent/dir/file.csv")
        
        # Test non-CSV extension warning
        with patch('builtins.print') as mock_print:
            with patch('os.path.exists', return_value=True):
                with patch('builtins.open', mock_open()):
                    exporter.export([], "/tmp/file.txt")
                    mock_print.assert_called_with("Warning: Output file should have .csv extension")

    def test_csv_handles_large_export(self, tmp_path):
        """Test CSV can handle large number of tracks efficiently."""
        exporter = CSVExporter()
        output_file = tmp_path / "test_large.csv"
        
        # Create 10000 tracks
        tracks = [
            Track(id=i, artist=f"Artist {i}", title=f"Title {i}")
            for i in range(10000)
        ]
        
        exporter.export(tracks, str(output_file))
        
        # Verify file was created and has correct row count
        with open(output_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            row_count = sum(1 for _ in reader)
            
            assert row_count == 10000

    def test_csv_file_overwrite_protection(self, tmp_path):
        """Test CSV exporter warns before overwriting existing file."""
        exporter = CSVExporter()
        output_file = tmp_path / "existing.csv"
        
        # Create existing file
        output_file.write_text("existing content")
        
        tracks = [Track(id=1, artist="New", title="Data")]
        
        # Should prompt for confirmation (mocked as yes)
        with patch('builtins.input', return_value='y'):
            exporter.export(tracks, str(output_file))
            
            # Verify file was overwritten
            with open(output_file, 'r', encoding='utf-8-sig') as f:
                content = f.read()
                assert "New" in content
                assert "existing content" not in content