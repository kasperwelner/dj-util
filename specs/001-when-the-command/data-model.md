# Data Model

**Feature**: Rekordbox Streaming Tag Exporter  
**Date**: 2025-09-29  
**Phase**: 1 - Design

## Entities

### Tag (MyTag)
Represents a Rekordbox MyTag that can be assigned to tracks. In Rekordbox 6, these are stored in the DjmdMyTag table.

**Attributes**:
- `id` (int): Unique identifier in Rekordbox database
- `name` (str): Display name of the tag (Seq field in database)
- `track_count` (int): Number of tracks with this tag (computed)

**Validation Rules**:
- `name` must not be empty
- `name` must be unique within the database

**Relationships**:
- Many-to-many with Track entities

### Track (Content)
Represents a music track in the Rekordbox library. In Rekordbox 6, tracks are stored in the DjmdContent table.

**Attributes**:
- `id` (int): Unique identifier in Rekordbox database (ID field)
- `artist` (str, optional): Track artist name (Artist field)
- `title` (str, optional): Track title (Title field)
- `folder_path` (str, optional): File system folder path (FolderPath field - empty for streaming tracks)
- `file_path` (str, optional): Full file path (FilePath field - contains streaming URI for streaming tracks)
- `file_size` (int): File size in bytes (FileSize field - 0 for streaming)
- `my_tags` (List[Tag]): Associated MyTags (from ContentMyTag junction table)
- `is_streaming` (bool): Computed property based on empty FolderPath

**Validation Rules**:
- At least one of `artist` or `title` should be present
- `is_streaming` is True when `FolderPath` is None or empty string
- Unicode characters in `artist` and `title` must be preserved

**Relationships**:
- Many-to-many with MyTag entities via ContentMyTag junction table

**Computed Properties**:
```python
@property
def is_streaming(self) -> bool:
    # Check FolderPath is empty (streaming tracks have no local folder)
    return not self.folder_path or self.folder_path.strip() == ""
```

### CSVExport
Represents the output file containing filtered track information.

**Attributes**:
- `file_path` (str): Output file location
- `tracks` (List[Track]): Filtered tracks to export
- `encoding` (str): Character encoding (default: 'utf-8-sig')
- `columns` (List[str]): Column headers ['ID', 'Artist', 'Title']

**Validation Rules**:
- `file_path` must be writable
- `file_path` should have .csv extension
- Parent directory must exist
- Warn if file already exists (prompt for overwrite)

**Methods**:
- `write()`: Exports tracks to CSV file
- `validate_path()`: Checks file path validity
- `format_row(track: Track)`: Formats track data for CSV row

### TagSelection
Represents the user's tag selection state during interactive selection.

**Attributes**:
- `available_tags` (List[Tag]): All MyTags from database
- `selected_tags` (Set[int]): IDs of selected MyTags
- `selection_required` (bool): True (at least one tag must be selected)

**Validation Rules**:
- `selected_tags` must not be empty when confirming
- Selected tag IDs must exist in `available_tags`

**Methods**:
- `toggle_tag(tag_id: int)`: Select/deselect a MyTag
- `validate_selection()`: Ensure at least one tag selected
- `get_selected_tags()`: Returns List[Tag] of selected MyTags

## State Transitions

### Export Workflow States
```
1. INIT
   ↓
2. DATABASE_CONNECTED
   ↓
3. TAGS_LOADED
   ↓
4. TAGS_SELECTED (requires validation)
   ↓
5. TRACKS_FILTERED
   ↓
6. EXPORT_READY
   ↓
7. EXPORT_COMPLETE | EXPORT_FAILED
```

### Error States
- `DATABASE_NOT_FOUND`: Rekordbox database file doesn't exist
- `DATABASE_LOCKED`: Database is in use by Rekordbox
- `NO_TAGS_SELECTED`: User attempted to proceed without selection
- `NO_MATCHING_TRACKS`: No streaming tracks match selected tags
- `EXPORT_PATH_INVALID`: Cannot write to specified location

## Data Flow

```
RekordboxDB → MyTag[] → TagSelection → MyTag[] (selected)
                ↓
RekordboxDB → Content[] → Filter(streaming) → Filter(MyTags) → Track[]
                                                   ↓
                                            CSVExport → file.csv
```

## Constraints

### Performance
- Tag loading: < 1 second for typical library
- Track filtering: Process 10k tracks in < 5 seconds
- CSV export: Stream writing for memory efficiency

### Data Integrity
- No data modification to Rekordbox database (read-only)
- Preserve all Unicode characters in export
- Maintain tag-track relationships accurately

### Scalability
- Support libraries with 100k+ tracks
- Handle 1000+ tags
- Export files up to 10MB without memory issues

## Example Data

### Sample MyTag
```json
{
  "id": 1,
  "name": "Deep House",
  "track_count": 245
}
```

### Sample Track (Streaming)
```json
{
  "id": 12345,
  "artist": "Disclosure",
  "title": "Latch feat. Sam Smith",
  "folder_path": "",
  "file_path": "beatport://tracks/12345",
  "file_size": 0,
  "my_tags": [1, 3, 7],
  "is_streaming": true
}
```

### Sample CSV Output
```csv
ID,Artist,Title
12345,Disclosure,Latch feat. Sam Smith
12346,Flume,Never Be Like You feat. Kai
12347,"Petit Biscuit",Sunset Lover
```

## Testing Considerations

### Unit Test Scenarios
- Tag with empty name validation
- Track with Unicode characters (Japanese, Emoji)
- Streaming detection with various folder_path values
- CSV escaping for quotes and commas

### Integration Test Scenarios
- Load MyTags from sample Rekordbox database
- Filter streaming tracks with multiple MyTags
- Export large dataset (memory test)
- Handle corrupted database gracefully