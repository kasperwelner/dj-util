"""RekordboxAdapter service for database interaction."""
import os
from pathlib import Path
from typing import List, Optional, Set
from src.models.tag import MyTag
from src.models.track import Track

try:
    from pyrekordbox import Rekordbox6Database
    PYREKORDBOX_AVAILABLE = True
except ImportError:
    PYREKORDBOX_AVAILABLE = False
    Rekordbox6Database = None


class RekordboxAdapter:
    """Adapter for interacting with Rekordbox database via pyrekordbox.
    
    Provides a clean interface for database operations and handles
    the complexity of the pyrekordbox library.
    """
    
    def __init__(self) -> None:
        """Initialize the adapter."""
        self.db: Optional[Rekordbox6Database] = None
        self.error_message: str = ""
        self.connected: bool = False
    
    def connect(self, db_path: Optional[str] = None) -> bool:
        """Connect to Rekordbox database.
        
        Args:
            db_path: Optional path to database. If None, auto-detect.
            
        Returns:
            True if connection successful, False otherwise
        """
        if not PYREKORDBOX_AVAILABLE:
            self.error_message = "pyrekordbox library not installed"
            return False
        
        if db_path is None:
            db_path = self._find_database()
            if db_path is None:
                self.error_message = "Database not found - please specify path"
                return False
        
        if not os.path.exists(db_path):
            self.error_message = f"Database file not found: {db_path}"
            return False
        
        try:
            # Check if file can be read first
            with open(db_path, 'rb') as f:
                # Just try to read the header to check access
                f.read(16)
        except PermissionError:
            self.error_message = "Database is locked - please close Rekordbox"
            return False
        except OSError as e:
            self.error_message = f"Cannot access database: {str(e)}"
            return False
        
        try:
            self.db = Rekordbox6Database(db_path)
            self.connected = True
            return True
        except Exception as e:
            # Check for common warning about Rekordbox running
            error_str = str(e).lower()
            if "running" in error_str or "locked" in error_str:
                self.error_message = "Database is locked - please close Rekordbox"
            else:
                self.error_message = f"Failed to connect: {str(e)}"
            return False
    
    def _find_database(self) -> Optional[str]:
        """Auto-detect Rekordbox database location.
        
        Returns:
            Path to database if found, None otherwise
        """
        home = Path.home()
        
        # Common locations for Rekordbox 6 database
        locations = [
            home / "Library" / "Pioneer" / "rekordbox" / "master.db",  # macOS
            home / "AppData" / "Roaming" / "Pioneer" / "rekordbox" / "master.db",  # Windows
            home / ".Pioneer" / "rekordbox" / "master.db",  # Linux
        ]
        
        for location in locations:
            if location.exists():
                return str(location)
        
        return None
    
    def get_all_mytags(self) -> List[MyTag]:
        """Get all MyTags from database.
        
        Returns:
            List of MyTag objects
        """
        if not self.connected or self.db is None:
            return []
        
        try:
            # Use get_my_tag() with underscore
            db_tags = self.db.get_my_tag()
            tags = []
            
            # Convert query to list and process
            for db_tag in db_tags:
                # Keep ID as string for consistency with database
                tag_id = str(db_tag.ID) if db_tag.ID is not None else ""
                
                tag = MyTag(
                    id=tag_id,  # Store as string
                    name=db_tag.Name,  # Name field contains the tag name
                    track_count=None  # Will be computed if needed
                )
                tags.append(tag)
            
            return tags
        except Exception as e:
            self.error_message = f"Failed to load tags: {str(e)}"
            return []
    
    def get_streaming_tracks(self) -> List[Track]:
        """Get all streaming tracks.
        
        Streaming tracks are identified by:
        - Empty FolderPath
        - FolderPath containing service names (Tidal, Beatport, Spotify, etc.)
        - ServiceID != 0 (if available)
        
        Returns:
            List of Track objects that are streaming tracks
        """
        if not self.connected or self.db is None:
            return []
        
        try:
            # Convert query to list to properly iterate
            all_content = list(self.db.get_content())
            streaming_tracks = []
            
            # Common streaming service indicators
            streaming_services = ['tidal', 'beatport', 'spotify', 'soundcloud', 
                                 'beatsource', 'apple music', 'youtube']
            
            for content in all_content:
                is_streaming = False
                
                # Check if FolderPath is empty or None
                if not content.FolderPath or content.FolderPath.strip() == "":
                    is_streaming = True
                # Check if path contains streaming service names
                elif content.FolderPath:
                    folder_lower = content.FolderPath.lower()
                    for service in streaming_services:
                        if service in folder_lower:
                            is_streaming = True
                            break
                
                # Check ServiceID if available (non-zero means streaming)
                if hasattr(content, 'ServiceID') and content.ServiceID and content.ServiceID != 0:
                    is_streaming = True
                
                if is_streaming:
                    track = self._content_to_track(content)
                    streaming_tracks.append(track)
            
            return streaming_tracks
        except Exception as e:
            self.error_message = f"Failed to load tracks: {str(e)}"
            return []
    
    def get_tracks_by_mytags(self, tag_ids: List[str]) -> List[Track]:
        """Get tracks that have any of the specified MyTags.
        
        Args:
            tag_ids: List of MyTag IDs (strings) to filter by
            
        Returns:
            List of Track objects with at least one of the tags
        """
        if not self.connected or self.db is None:
            return []
        
        try:
            # Use get_my_tag_songs() to get content-tag relationships
            my_tag_songs = self.db.get_my_tag_songs()
            
            # Find content IDs with matching tags (compare as strings)
            content_ids = set()
            tag_ids_str = [str(tid) for tid in tag_ids]  # Ensure all are strings
            for mts in my_tag_songs:
                if str(mts.MyTagID) in tag_ids_str:
                    content_ids.add(mts.ContentID)
            
            # Get the actual content
            tracks = []
            all_content = list(self.db.get_content())  # Get all content once
            
            for content in all_content:
                if content.ID in content_ids:
                    track = self._content_to_track(content)
                    tracks.append(track)
            
            return tracks
        except Exception as e:
            self.error_message = f"Failed to filter tracks: {str(e)}"
            return []
    
    def get_streaming_tracks_by_tags(self, tag_ids: List[str]) -> List[Track]:
        """Get streaming tracks that have any of the specified MyTags.
        
        Args:
            tag_ids: List of MyTag IDs (strings) to filter by
            
        Returns:
            List of streaming Track objects with at least one of the tags
        """
        tracks = self.get_tracks_by_mytags(tag_ids)
        return [track for track in tracks if track.is_streaming]
    
    def _content_to_track(self, content) -> Track:
        """Convert pyrekordbox content object to Track model.
        
        Args:
            content: pyrekordbox DjmdContent object
            
        Returns:
            Track model instance
        """
        # Get tag IDs for this track (as strings)
        tag_ids = []
        if hasattr(content, 'MyTagIDs') and content.MyTagIDs:
            tag_ids = [str(tid) for tid in content.MyTagIDs]
        elif hasattr(content, 'MyTags') and content.MyTags:
            tag_ids = [str(tag.ID) for tag in content.MyTags]
        
        # Handle potential None values
        folder_path = content.FolderPath if content.FolderPath else ""
        # Note: Rekordbox 6 doesn't have separate FilePath, FolderPath contains the full path
        file_path = folder_path  # Use FolderPath as file_path
        
        # Extract artist name (might be an object with Name attribute)
        artist_name = ""
        if content.Artist:
            if hasattr(content.Artist, 'Name'):
                artist_name = content.Artist.Name
            else:
                artist_name = str(content.Artist)
        
        return Track(
            id=content.ID,
            artist=artist_name,
            title=content.Title or "",
            folder_path=folder_path,
            file_path=file_path,
            file_size=content.FileSize or 0,
            my_tag_ids=tag_ids
        )
    
    def close(self) -> None:
        """Close database connection."""
        if self.db:
            # pyrekordbox doesn't require explicit close, but we clear reference
            self.db = None
            self.connected = False