"""Path utility functions for file operations."""
import re
import unicodedata
from pathlib import Path
from typing import Optional


def normalize_path(path: str) -> Path:
    """Normalize path for Rekordbox compatibility.
    
    Args:
        path: Input path string
        
    Returns:
        Normalized absolute Path object
    """
    # Expand user home directory
    path_obj = Path(path).expanduser()
    
    # Convert to absolute path
    path_obj = path_obj.resolve()
    
    # Normalize unicode to NFC (macOS compatibility)
    normalized_str = unicodedata.normalize('NFC', str(path_obj))
    
    return Path(normalized_str)


def sanitize_filename(name: str) -> str:
    """Remove invalid filename characters.
    
    Args:
        name: Filename to sanitize
        
    Returns:
        Sanitized filename
    """
    # Replace invalid characters with underscore
    invalid_chars = r'[/\\:*?"<>|]'
    sanitized = re.sub(invalid_chars, '_', name)
    
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')
    
    # Limit length (255 chars is common filesystem limit)
    if len(sanitized) > 200:  # Leave room for extension and parent dirs
        sanitized = sanitized[:200]
    
    return sanitized


def build_library_path(
    copy_dir: Path,
    artist: str,
    title: str,
    extension: str
) -> Path:
    """Build organized library path.
    
    Structure: <copy_dir>/<Artist>/<Artist> - <Title>.<ext>
    
    Args:
        copy_dir: Root library directory
        artist: Artist name
        title: Track title
        extension: File extension (without dot)
        
    Returns:
        Full path for the file
    """
    # Sanitize components
    safe_artist = sanitize_filename(artist) if artist else "Unknown Artist"
    safe_title = sanitize_filename(title) if title else "Unknown Title"
    
    # Build path components
    artist_dir = copy_dir / safe_artist
    filename = f"{safe_artist} - {safe_title}.{extension}"
    
    return artist_dir / filename


def handle_duplicate_filename(path: Path) -> Path:
    """Add (1), (2), etc. if file exists.
    
    Args:
        path: Desired file path
        
    Returns:
        Path that doesn't exist (may have number appended)
    """
    if not path.exists():
        return path
    
    # Split into stem and extension
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    
    # Try numbered variants
    counter = 1
    while True:
        new_path = parent / f"{stem} ({counter}){suffix}"
        if not new_path.exists():
            return new_path
        counter += 1
        
        # Safety limit
        if counter > 1000:
            raise ValueError(f"Too many duplicate files for: {path}")
