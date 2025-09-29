"""Validators for path and selection validation."""
import os
from pathlib import Path
from typing import List, Optional, Tuple


def validate_database_path(path: Optional[str] = None) -> Tuple[bool, str]:
    """Validate Rekordbox database path.
    
    Args:
        path: Database path to validate, None to auto-detect
        
    Returns:
        Tuple of (is_valid, error_message/path)
    """
    if path is None:
        # Try to auto-detect
        detected = find_rekordbox_database()
        if detected:
            return True, detected
        return False, "Could not auto-detect Rekordbox database. Please specify path with --db-path"
    
    # Check if path exists
    db_path = Path(path)
    if not db_path.exists():
        return False, f"Database file not found: {path}"
    
    if not db_path.is_file():
        return False, f"Path is not a file: {path}"
    
    # Check if it's likely a Rekordbox database
    if db_path.suffix != '.db' and db_path.name != 'master.db':
        return False, f"File does not appear to be a Rekordbox database: {path}"
    
    return True, str(db_path.absolute())


def find_rekordbox_database() -> Optional[str]:
    """Auto-detect Rekordbox database location.
    
    Returns:
        Path to database if found, None otherwise
    """
    home = Path.home()
    
    # Platform-specific default locations
    locations = [
        # macOS
        home / "Library" / "Pioneer" / "rekordbox" / "master.db",
        # Windows
        home / "AppData" / "Roaming" / "Pioneer" / "rekordbox" / "master.db",
        # Linux
        home / ".Pioneer" / "rekordbox" / "master.db",
    ]
    
    for location in locations:
        if location.exists() and location.is_file():
            return str(location)
    
    return None


def validate_output_path(path: str) -> Tuple[bool, str]:
    """Validate CSV output path.
    
    Args:
        path: Output path to validate
        
    Returns:
        Tuple of (is_valid, error_message/resolved_path)
    """
    output_path = Path(path)
    
    # Check extension
    if output_path.suffix.lower() != '.csv':
        return False, "Output file must have .csv extension"
    
    # Resolve to absolute path
    output_path = output_path.absolute()
    
    # Check if parent directory exists or can be created
    parent = output_path.parent
    if not parent.exists():
        try:
            parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            return False, f"Cannot create output directory: {e}"
    
    # Check if file already exists
    if output_path.exists():
        # This is a warning, not an error - caller can decide to overwrite
        return True, f"Warning: File already exists and will be overwritten: {output_path}"
    
    # Check write permissions
    test_file = parent / '.write_test'
    try:
        test_file.touch()
        test_file.unlink()
    except OSError:
        return False, f"No write permission in directory: {parent}"
    
    return True, str(output_path)


def validate_tag_selection(
    selected_ids: List[str],
    available_ids: List[str]
) -> Tuple[bool, str]:
    """Validate that selected tag IDs are valid.
    
    Args:
        selected_ids: List of selected tag IDs
        available_ids: List of available tag IDs
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not selected_ids:
        return False, "No tags selected"
    
    # Check for invalid IDs
    available_set = set(available_ids)
    invalid_ids = [sid for sid in selected_ids if sid not in available_set]
    
    if invalid_ids:
        return False, f"Invalid tag IDs: {invalid_ids}"
    
    return True, "Valid selection"


def validate_limit(limit: Optional[int]) -> Tuple[bool, str]:
    """Validate the --limit parameter.
    
    Args:
        limit: Limit value to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if limit is None:
        return True, "No limit"
    
    if limit <= 0:
        return False, "Limit must be a positive integer"
    
    if limit > 100000:
        return False, "Limit too large (max 100000)"
    
    return True, f"Limit: {limit}"


def sanitize_filename(name: str, max_length: int = 50) -> str:
    """Sanitize a string for use in filenames.
    
    Args:
        name: String to sanitize
        max_length: Maximum length of result
        
    Returns:
        Sanitized string safe for filenames
    """
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    
    # Remove control characters
    name = ''.join(char for char in name if ord(char) >= 32)
    
    # Trim whitespace and limit length
    name = name.strip()[:max_length]
    
    # Ensure not empty
    if not name:
        name = 'unnamed'
    
    return name


def validate_unicode_support() -> bool:
    """Check if the system supports Unicode properly.
    
    Returns:
        True if Unicode is properly supported
    """
    try:
        # Test with Japanese and emoji
        test_string = "テスト 🎵"
        encoded = test_string.encode('utf-8')
        decoded = encoded.decode('utf-8')
        return decoded == test_string
    except (UnicodeEncodeError, UnicodeDecodeError):
        return False