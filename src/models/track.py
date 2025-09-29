"""Track model representing a music track in Rekordbox."""
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Track:
    """Represents a music track in the Rekordbox library.
    
    In Rekordbox 6, tracks are stored in the DjmdContent table.
    Streaming tracks are identified by empty FolderPath field.
    """
    
    id: int
    artist: Optional[str] = None
    title: Optional[str] = None
    folder_path: Optional[str] = None
    file_path: Optional[str] = None
    file_size: int = 0
    my_tag_ids: List[str] = field(default_factory=list)  # Store as strings to match database
    
    def __post_init__(self) -> None:
        """Validate track after initialization."""
        # At least one of artist or title should be present
        if not self.artist and not self.title:
            # Allow both to be None/empty for edge cases, but warn
            pass  # Tracks with missing metadata are valid but unusual
        
        # Ensure file_size is non-negative
        if self.file_size < 0:
            raise ValueError("File size cannot be negative")
    
    @property
    def is_streaming(self) -> bool:
        """Check if track is a streaming track.
        
        Streaming tracks are identified by:
        - Empty FolderPath
        - FolderPath containing streaming service names
        """
        if not self.folder_path or self.folder_path.strip() == "":
            return True
        
        # Check for streaming services in path
        streaming_services = ['tidal', 'beatport', 'spotify', 'soundcloud', 
                             'beatsource', 'apple music', 'youtube']
        folder_lower = self.folder_path.lower()
        
        for service in streaming_services:
            if service in folder_lower:
                return True
        
        return False
    
    @property
    def display_name(self) -> str:
        """Get a display name for the track."""
        if self.artist and self.title:
            return f"{self.artist} - {self.title}"
        elif self.title:
            return self.title
        elif self.artist:
            return f"{self.artist} - Unknown Title"
        else:
            return f"Track {self.id}"
    
    def has_tag(self, tag_id: str) -> bool:
        """Check if track has a specific tag."""
        return str(tag_id) in [str(tid) for tid in self.my_tag_ids]
    
    def has_any_tag(self, tag_ids: List[str]) -> bool:
        """Check if track has any of the specified tags."""
        return any(self.has_tag(tag_id) for tag_id in tag_ids)
    
    def to_csv_row(self) -> dict:
        """Convert track to CSV row format."""
        return {
            'id': str(self.id),
            'artist': self.artist or '',
            'title': self.title or '',
            'streaming': 'Yes' if self.is_streaming else 'No'
        }
    
    def __str__(self) -> str:
        """String representation of the track."""
        streaming_marker = " [STREAMING]" if self.is_streaming else ""
        return f"{self.display_name}{streaming_marker}"
    
    def __repr__(self) -> str:
        """Developer representation of the track."""
        return (f"Track(id={self.id}, artist='{self.artist}', title='{self.title}', "
                f"is_streaming={self.is_streaming}, tags={self.my_tag_ids})")
    
    def __eq__(self, other: object) -> bool:
        """Check equality based on ID."""
        if not isinstance(other, Track):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Make track hashable based on ID."""
        return hash(self.id)