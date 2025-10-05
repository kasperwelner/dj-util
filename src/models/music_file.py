"""Music file model for file matching."""
from dataclasses import dataclass


@dataclass
class MusicFile:
    """Represents a music file found during scanning."""
    file_path: str
    filename: str
    filename_clean: str  # Cleaned for matching
