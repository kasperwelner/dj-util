"""Contract tests for pyrekordbox database integration."""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Optional

from src.services.rekordbox import RekordboxAdapter


class TestRekordboxContract:
    """Test contract with pyrekordbox library."""

    def test_database_connection_succeeds_with_valid_path(self):
        """Test that RekordboxAdapter can connect to a valid database."""
        # This test MUST fail initially
        adapter = RekordboxAdapter()
        mock_db_path = "/path/to/rekordbox.db"
        
        with patch("pyrekordbox.Rekordbox6Database") as mock_db:
            mock_db.return_value = Mock()
            result = adapter.connect(mock_db_path)
            
            assert result is True
            mock_db.assert_called_once_with(mock_db_path)

    def test_database_connection_fails_with_invalid_path(self):
        """Test that RekordboxAdapter handles invalid database path."""
        adapter = RekordboxAdapter()
        invalid_path = "/nonexistent/path.db"
        
        result = adapter.connect(invalid_path)
        assert result is False

    def test_get_all_mytags_returns_tag_list(self):
        """Test that we can retrieve all MyTags from database."""
        adapter = RekordboxAdapter()
        
        with patch.object(adapter, 'db') as mock_db:
            mock_tag1 = Mock(ID=1, Seq="Deep House")
            mock_tag2 = Mock(ID=2, Seq="Techno")
            mock_db.get_mytag.return_value = [mock_tag1, mock_tag2]
            
            tags = adapter.get_all_mytags()
            
            assert len(tags) == 2
            assert tags[0].name == "Deep House"
            assert tags[1].name == "Techno"

    def test_get_streaming_tracks_filters_by_empty_folderpath(self):
        """Test that streaming tracks are identified by empty FolderPath."""
        adapter = RekordboxAdapter()
        
        with patch.object(adapter, 'db') as mock_db:
            mock_track1 = Mock(ID=1, Title="Track 1", FolderPath="")
            mock_track2 = Mock(ID=2, Title="Track 2", FolderPath="/local/path")
            mock_track3 = Mock(ID=3, Title="Track 3", FolderPath="")
            mock_db.get_content.return_value = [mock_track1, mock_track2, mock_track3]
            
            streaming_tracks = adapter.get_streaming_tracks()
            
            assert len(streaming_tracks) == 2
            assert all(track.is_streaming for track in streaming_tracks)

    def test_get_tracks_by_mytags_uses_junction_table(self):
        """Test that tracks are filtered by MyTags using ContentMyTag junction."""
        adapter = RekordboxAdapter()
        tag_ids = [1, 3]
        
        with patch.object(adapter, 'db') as mock_db:
            # Mock junction table relationships
            mock_content_tag1 = Mock(ContentID=100, MyTagID=1)
            mock_content_tag2 = Mock(ContentID=101, MyTagID=3)
            mock_db.get_content_mytag.return_value = [mock_content_tag1, mock_content_tag2]
            
            # Mock content retrieval
            mock_track1 = Mock(ID=100, Title="Track A", FolderPath="")
            mock_track2 = Mock(ID=101, Title="Track B", FolderPath="")
            mock_db.get_content_by_id = Mock(side_effect=[mock_track1, mock_track2])
            
            tracks = adapter.get_tracks_by_mytags(tag_ids)
            
            assert len(tracks) == 2
            assert tracks[0].id == 100
            assert tracks[1].id == 101

    def test_handles_database_locked_error(self):
        """Test graceful handling when database is locked by Rekordbox."""
        adapter = RekordboxAdapter()
        
        with patch("pyrekordbox.Rekordbox6Database") as mock_db:
            mock_db.side_effect = PermissionError("Database is locked")
            
            result = adapter.connect("/path/to/rekordbox.db")
            assert result is False
            assert adapter.error_message == "Database is locked - please close Rekordbox"

    def test_handles_unicode_in_track_names(self):
        """Test that Unicode characters in artist/title are preserved."""
        adapter = RekordboxAdapter()
        
        with patch.object(adapter, 'db') as mock_db:
            mock_track = Mock(
                ID=1,
                Artist="日本人アーティスト",
                Title="Москва 🎵",
                FolderPath=""
            )
            mock_db.get_content.return_value = [mock_track]
            
            tracks = adapter.get_streaming_tracks()
            
            assert len(tracks) == 1
            assert tracks[0].artist == "日本人アーティスト"
            assert tracks[0].title == "Москва 🎵"