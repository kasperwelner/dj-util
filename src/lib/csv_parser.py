"""CSV parser for track mapping files."""
import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional
from src.lib.path_utils import normalize_path


@dataclass
class TrackMapping:
    """Represents a row from the CSV mapping file."""
    artist: str
    title: str
    file_path: Path
    rekordbox_id: Optional[int] = None  # Optional if using fuzzy matching
    
    # Computed fields
    normalized_path: Optional[Path] = None
    file_exists: bool = False
    file_size: int = 0
    
    # Fuzzy matching fields (populated when --no-id-match)
    matched_track_id: Optional[int] = None
    match_confidence: Optional[float] = None
    match_ambiguous: bool = False


class CSVParser:
    """Parse and validate CSV mapping files."""
    
    COLUMN_ALIASES = {
        'rekordbox_id': ['rekordboxid', 'recordboxid', 'id'],
        'artist': ['artist'],
        'title': ['title', 'song title', 'song name'],
        'file_path': ['file path', 'path', 'filepath']
    }
    
    def __init__(self, require_id: bool = True):
        """Initialize parser.
        
        Args:
            require_id: If True, require rekordbox_id column. If False, ID is optional.
        """
        self.require_id = require_id
    
    def parse(self, csv_path: str) -> List[TrackMapping]:
        """Parse CSV and return validated track mappings.
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            List of TrackMapping objects
            
        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If CSV format is invalid
        """
        csv_file = Path(csv_path)
        if not csv_file.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        mappings = []
        
        with open(csv_file, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            
            if not reader.fieldnames:
                raise ValueError("CSV file is empty or has no headers")
            
            # Validate and map headers
            column_map = self.validate_headers(list(reader.fieldnames))
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is 1)
                try:
                    mapping = self._parse_row(row, column_map, row_num)
                    mappings.append(mapping)
                except Exception as e:
                    raise ValueError(f"Error parsing row {row_num}: {e}")
        
        return mappings
    
    def validate_headers(self, headers: List[str]) -> Dict[str, str]:
        """Map flexible headers to canonical field names.
        
        Args:
            headers: List of column names from CSV
            
        Returns:
            Dict mapping canonical names to actual column names
            
        Raises:
            ValueError: If required columns missing
        """
        # Normalize headers (lowercase, strip whitespace)
        normalized_headers = {h.lower().strip(): h for h in headers}
        
        column_map = {}
        
        # Map each canonical field to actual column name
        for canonical, aliases in self.COLUMN_ALIASES.items():
            found = False
            for alias in aliases:
                if alias.lower() in normalized_headers:
                    column_map[canonical] = normalized_headers[alias.lower()]
                    found = True
                    break
            
            # Check if required field is missing
            if not found:
                if canonical == 'rekordbox_id' and not self.require_id:
                    # ID is optional when fuzzy matching
                    continue
                elif canonical in ['artist', 'title', 'file_path']:
                    # These are always required
                    raise ValueError(
                        f"Required column '{canonical}' not found. "
                        f"Expected one of: {', '.join(aliases)}"
                    )
        
        return column_map
    
    def _parse_row(
        self,
        row: Dict[str, str],
        column_map: Dict[str, str],
        row_num: int
    ) -> TrackMapping:
        """Parse a single CSV row.
        
        Args:
            row: Dict of column values
            column_map: Mapping of canonical to actual column names
            row_num: Row number (for error messages)
            
        Returns:
            TrackMapping object
            
        Raises:
            ValueError: If row data is invalid
        """
        # Extract required fields
        artist = row.get(column_map['artist'], '').strip()
        title = row.get(column_map['title'], '').strip()
        file_path_str = row.get(column_map['file_path'], '').strip()
        
        if not artist:
            raise ValueError(f"Artist is empty in row {row_num}")
        if not title:
            raise ValueError(f"Title is empty in row {row_num}")
        if not file_path_str:
            raise ValueError(f"File path is empty in row {row_num}")
        
        # Parse optional ID
        rekordbox_id = None
        if 'rekordbox_id' in column_map:
            id_str = row.get(column_map['rekordbox_id'], '').strip()
            if id_str:
                try:
                    rekordbox_id = int(id_str)
                except ValueError:
                    raise ValueError(
                        f"Invalid Rekordbox ID '{id_str}' in row {row_num} "
                        f"(must be an integer)"
                    )
        
        # Normalize and validate file path
        try:
            normalized_path = normalize_path(file_path_str)
        except Exception as e:
            raise ValueError(f"Invalid file path in row {row_num}: {e}")
        
        file_exists = normalized_path.exists()
        file_size = normalized_path.stat().st_size if file_exists else 0
        
        return TrackMapping(
            artist=artist,
            title=title,
            file_path=Path(file_path_str),  # Keep original for display
            rekordbox_id=rekordbox_id,
            normalized_path=normalized_path,
            file_exists=file_exists,
            file_size=file_size
        )
