"""CSVExporter service for exporting tracks to CSV format."""
import csv
import os
from pathlib import Path
from typing import List, Optional
from src.models.track import Track
from src.models.csv_export import CSVExport


class CSVExporter:
    """Service for exporting track data to CSV files.
    
    Handles Unicode properly with UTF-8-sig encoding for Excel compatibility.
    """
    
    def __init__(self):
        """Initialize the CSV exporter."""
        self.last_export: Optional[CSVExport] = None
    
    def export_tracks(
        self,
        tracks: List[Track],
        output_path: str,
        tag_names: Optional[List[str]] = None
    ) -> CSVExport:
        """Export tracks to CSV file.
        
        Args:
            tracks: List of tracks to export
            output_path: Path to output CSV file
            tag_names: Optional list of tag names for metadata
            
        Returns:
            CSVExport object with export details
            
        Raises:
            ValueError: If output path is invalid
            IOError: If file cannot be written
        """
        # Validate output path
        output_file = Path(output_path)
        
        # Ensure directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create export record
        export = CSVExport(
            file_path=str(output_file.absolute()),
            tracks=tracks
        )
        
        try:
            # Write CSV with UTF-8-sig encoding for Excel compatibility
            with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
                # Define field names
                fieldnames = ['artist', 'title', 'streaming']
                
                # Create DictWriter
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Write header
                writer.writeheader()
                
                # Write track data
                for track in tracks:
                    writer.writerow({
                        'artist': track.artist or '',
                        'title': track.title or '',
                        'streaming': 'Yes' if track.is_streaming else 'No'
                    })
            
            # Store successful export
            self.last_export = export
            
            return export
            
        except IOError as e:
            raise IOError(f"Failed to export to {output_path}: {e}")
        except Exception as e:
            raise
    
    def export_summary(self, export: CSVExport) -> str:
        """Generate a summary of the export.
        
        Args:
            export: CSVExport object to summarize
            
        Returns:
            Human-readable summary string
        """
        lines = []
        lines.append(f"Export Summary:")
        lines.append(f"  File: {export.file_path}")
        lines.append(f"  Tracks exported: {export.track_count}")
        
        if export.tag_names:
            lines.append(f"  Tags: {', '.join(export.tag_names)}")
        
        if export.file_exists():
            lines.append(f"  Status: Export completed")
        else:
            lines.append(f"  Status: File not created")
        
        return '\n'.join(lines)
    
    def validate_output_path(self, path: str) -> bool:
        """Validate that the output path is writable.
        
        Args:
            path: Path to validate
            
        Returns:
            True if path is valid and writable
        """
        try:
            output_file = Path(path)
            
            # Check if path has CSV extension
            if output_file.suffix.lower() != '.csv':
                return False
            
            # Check if parent directory exists or can be created
            if not output_file.parent.exists():
                try:
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                except OSError:
                    return False
            
            # Check if we can write to the directory
            test_file = output_file.parent / '.test_write'
            try:
                test_file.touch()
                test_file.unlink()
                return True
            except OSError:
                return False
                
        except Exception:
            return False
    
    def get_default_filename(self, tag_names: Optional[List[str]] = None) -> str:
        """Generate a default filename based on tags and timestamp.
        
        Args:
            tag_names: Optional list of tag names to include in filename
            
        Returns:
            Suggested filename
        """
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if tag_names:
            # Sanitize tag names for filename
            safe_tags = []
            for tag in tag_names[:3]:  # Limit to first 3 tags
                safe_tag = "".join(c for c in tag if c.isalnum() or c in (' ', '-', '_'))
                safe_tags.append(safe_tag.strip())
            
            if safe_tags:
                tag_part = "_".join(safe_tags).replace(" ", "_")
                return f"rekordbox_export_{tag_part}_{timestamp}.csv"
        
        return f"rekordbox_export_{timestamp}.csv"