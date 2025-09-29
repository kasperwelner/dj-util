"""CSVExport model for managing CSV export operations."""
import os
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field


@dataclass
class CSVExport:
    """Represents a CSV export operation.
    
    Handles file path validation, column configuration,
    and encoding settings for proper Unicode support.
    """
    
    file_path: str
    tracks: List = field(default_factory=list)
    encoding: str = 'utf-8-sig'  # UTF-8 with BOM for Excel compatibility
    columns: List[str] = field(default_factory=lambda: ['ID', 'Artist', 'Title'])
    
    def __post_init__(self) -> None:
        """Validate export configuration after initialization."""
        self.file_path = str(Path(self.file_path).resolve())
        self.validate_path()
    
    def validate_path(self) -> None:
        """Check if the output path is valid and writable.
        
        Raises:
            ValueError: If path is invalid or not writable
        """
        path = Path(self.file_path)
        parent_dir = path.parent
        
        # Check if parent directory exists
        if not parent_dir.exists():
            raise ValueError(f"Output directory does not exist: {parent_dir}")
        
        # Check if parent directory is writable
        if not os.access(parent_dir, os.W_OK):
            raise ValueError(f"Output directory is not writable: {parent_dir}")
        
        # Warn if file doesn't have .csv extension
        if path.suffix.lower() != '.csv':
            print(f"Warning: Output file should have .csv extension, got: {path.suffix}")
    
    def file_exists(self) -> bool:
        """Check if the output file already exists."""
        return Path(self.file_path).exists()
    
    def should_overwrite(self, force: bool = False) -> bool:
        """Determine if existing file should be overwritten.
        
        Args:
            force: If True, always overwrite without prompting
            
        Returns:
            True if file should be overwritten
        """
        if not self.file_exists():
            return True
        
        if force:
            return True
        
        # Prompt user for confirmation
        response = input(f"File {self.file_path} already exists. Overwrite? (y/n): ")
        return response.lower().strip() in ('y', 'yes')
    
    @property
    def track_count(self) -> int:
        """Get the number of tracks to export."""
        return len(self.tracks)
    
    @property
    def is_empty(self) -> bool:
        """Check if there are no tracks to export."""
        return self.track_count == 0
    
    def get_stats(self) -> dict:
        """Get export statistics."""
        return {
            'file_path': self.file_path,
            'track_count': self.track_count,
            'encoding': self.encoding,
            'columns': self.columns,
            'file_exists': self.file_exists()
        }
    
    def __str__(self) -> str:
        """String representation of the export."""
        return f"CSVExport({self.track_count} tracks -> {self.file_path})"
    
    def __repr__(self) -> str:
        """Developer representation of the export."""
        return (f"CSVExport(file_path='{self.file_path}', tracks={self.track_count}, "
                f"encoding='{self.encoding}')")