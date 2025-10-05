"""Track record model for file matching."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class TrackRecord:
    """Represents a track from the CSV file."""
    rekordbox_id: str
    artist: str
    title: str
    streaming: str
    matched_file_path: Optional[str] = None
    confidence_score: float = 0.0
