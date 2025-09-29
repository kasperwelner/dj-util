"""MyTag model representing a Rekordbox tag."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class MyTag:
    """Represents a Rekordbox MyTag that can be assigned to tracks.
    
    In Rekordbox 6, these are stored in the DjmdMyTag table.
    Tags do NOT have color attributes in Rekordbox MyTags.
    """
    
    id: str  # Store as string to match database format
    name: str
    track_count: Optional[int] = None
    
    def __post_init__(self) -> None:
        """Validate tag after initialization."""
        if not self.name or not self.name.strip():
            raise ValueError("Tag name cannot be empty")
        
        # Ensure name is stripped of whitespace
        self.name = self.name.strip()
        
        if self.track_count is not None and self.track_count < 0:
            raise ValueError("Track count cannot be negative")
    
    def __str__(self) -> str:
        """String representation of the tag."""
        count_str = f" ({self.track_count} tracks)" if self.track_count is not None else ""
        return f"{self.name}{count_str}"
    
    def __repr__(self) -> str:
        """Developer representation of the tag."""
        return f"MyTag(id={self.id}, name='{self.name}', track_count={self.track_count})"
    
    def __eq__(self, other: object) -> bool:
        """Check equality based on ID."""
        if not isinstance(other, MyTag):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Make tag hashable based on ID."""
        return hash(str(self.id))
