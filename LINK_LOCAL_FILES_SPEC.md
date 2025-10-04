# Link Local Files Feature Specification

## Overview

The `rekordbox link-local` command converts streaming tracks in Rekordbox to local file references by updating the database to point to files on disk. It supports optional audio format conversion, file copying to a managed library location, and provides comprehensive safety mechanisms including dry-run mode and database backups.

---

## High-Level Spec

### Purpose
Convert streaming tracks in Rekordbox (Tidal, Beatport, Spotify, etc.) to local file tracks by:
1. Reading a CSV mapping of Rekordbox track IDs to local file paths
2. Optionally converting audio files to a target format
3. Updating the Rekordbox database to reference the local files instead of streaming sources

### Key Features
- **CSV-driven mapping**: Maps Rekordbox IDs to local file paths
- **Audio format conversion**: Convert specified formats (e.g., FLAC, WAV) to a target format (e.g., MP3, AAC)
- **Managed library mode**: Copy/convert files into a structured library directory
- **Safety first**: Dry-run by default, database backups, transaction-based updates
- **Comprehensive reporting**: Detailed success/failure logs in console and optional Markdown report

### User Journey
```bash
# Step 1: Export streaming tracks and match with local files
rekordbox --tags "To Purchase" --output streaming_tracks.csv
python3 file_path_matcher.py -i streaming_tracks.csv -s ~/Music -o matched_tracks.csv

# Step 2: Link local files (dry-run first to preview)
rekordbox link-local --csv matched_tracks.csv

# Step 3: Review output, then apply with conversion
rekordbox link-local --csv matched_tracks.csv --apply \
  --convert-from flac,wav --convert-to mp3 \
  --copy-into ~/Music/Rekordbox-Library
```

---

## Detailed Specification

### Command: `rekordbox link-local`

#### Required Arguments
- `--csv PATH`: Path to CSV file with columns: `rekordboxId`, `artist`, `song title`, `file path`

#### Conversion Options
- `--convert-from FORMATS`: Comma-separated list of source formats to convert (e.g., `flac,wav,aiff`)
  - If file extension matches, it will be converted to target format
  - If not in list, file is used as-is (no conversion)
  - Case-insensitive matching
  - Default: none (no conversion)
  
- `--convert-to FORMAT`: Target format for conversion (e.g., `mp3`, `aac`, `m4a`)
  - Requires `--convert-from` to be specified
  - Must be a format supported by ffmpeg
  - Default: none

- `--conversion-quality PRESET`: Quality preset for conversion
  - Options: `low`, `medium`, `high`, `lossless`
  - Translates to codec-specific settings (bitrate, VBR level, etc.)
  - Default: `high`

#### Library Management Options
- `--copy-into DIR`: Copy/convert files into a managed library directory
  - Structure: `<DIR>/<Artist>/<Artist> - <Title>.<ext>`
  - Sanitizes filenames (removes special chars, handles duplicates)
  - If not specified, links to original file location
  - Default: none (reference in place)

- `--move`: Move files instead of copying (only valid with `--copy-into`)
  - Removes original file after successful copy/conversion
  - Default: false

#### Safety Options
- `--dry-run`: Preview changes without writing to database or converting files
  - Shows what would be updated, converted, copied
  - **Default: true** (must explicitly use `--apply` to execute)
  
- `--apply`: Execute the changes (disables dry-run)
  - Required to actually write to database
  - Default: false

- `--backup-db`: Create timestamped backup of master.db before changes
  - Backup location: `<db_dir>/master.db.backup.<timestamp>`
  - Default: true

- `--no-backup-db`: Skip database backup (not recommended)

#### Operational Options
- `--report PATH`: Write detailed Markdown report of all operations
  - Includes: updated tracks, skipped tracks, conversion details, errors
  - Default: none (console output only)

- `--strict`: Fail entire operation on first error
  - Rolls back all changes in database transaction
  - Default: false (continue on errors, report at end)

- `--limit N`: Process only first N rows (useful for testing)
  - Default: none (process all)

- `--db-path PATH`: Explicit path to Rekordbox database
  - Default: auto-detect (~/Library/Pioneer/rekordbox/master.db on macOS)

#### Validation Options
- `--allow-mismatch`: Proceed even if CSV artist/title don't match database
  - Logs warning but continues
  - Default: false (skip mismatched tracks)

- `--force`: Update tracks even if they appear to already be local
  - Default: false (skip already-local tracks)

#### Matching Options
- `--no-id-match`: Use fuzzy artist/title matching instead of Rekordbox IDs
  - CSV doesn't need `rekordboxId` column
  - Matches tracks using artist + title similarity (like bandcamp_wishlist_automator.py)
  - Uses combined similarity score with configurable threshold
  - Default: false (require ID column)

- `--match-threshold FLOAT`: Similarity threshold for fuzzy matching (0.0-1.0)
  - Only used when `--no-id-match` is enabled
  - Higher values = stricter matching (fewer false positives)
  - Lower values = looser matching (more matches, more false positives)
  - Default: 0.75

### CSV Format

#### Required Columns
The CSV must contain these columns (case-insensitive, flexible naming):

| Column Name Variants | Description | Required? | Example |
|---------------------|-------------|-----------|----------|
| `rekordboxId`, `RecordboxId`, `id` | Rekordbox track ID (integer) | Optional with `--no-id-match` | `130248411` |
| `artist`, `Artist` | Artist name | **Always required** | `Leod` |
| `song title`, `title`, `Song Name` | Track title | **Always required** | `Untitled 05` |
| `file path`, `path`, `File Path` | Absolute or relative path to audio file | **Always required** | `/Users/user/Music/Leod - Untitled 05.flac` |

#### CSV Example (with IDs - default mode)
```csv
rekordboxId,artist,song title,file path
130248411,Leod,Untitled 05,/Users/user/Music/Leod - Untitled 05.flac
181447005,KVLR,6am,/Users/user/Music/KVLR - 6am.wav
2427324,ALIVEMAEX,In Heaven with You,/Users/user/Music/ALIVEMAEX - In Heaven.mp3
```

#### CSV Example (without IDs - with `--no-id-match`)
```csv
artist,song title,file path
Leod,Untitled 05,/Users/user/Music/Leod - Untitled 05.flac
KVLR,6am,/Users/user/Music/KVLR - 6am.wav
ALIVEMAEX,In Heaven with You,/Users/user/Music/ALIVEMAEX - In Heaven.mp3
```

### Audio Conversion Details

#### Supported Formats
**Input formats** (via ffmpeg):
- Lossless: `flac`, `wav`, `aiff`, `alac`, `ape`, `wv`
- Lossy: `mp3`, `aac`, `m4a`, `ogg`, `opus`, `wma`

**Output formats**:
- `mp3`: MPEG Layer 3
- `aac`: Advanced Audio Coding
- `m4a`: MPEG-4 Audio (AAC container)
- `flac`: Free Lossless Audio Codec
- `wav`: Waveform Audio
- `aiff`: Audio Interchange File Format

#### Quality Presets

| Preset | MP3 | AAC | FLAC |
|--------|-----|-----|------|
| `low` | 128 kbps CBR | 96 kbps VBR | N/A (lossless) |
| `medium` | 192 kbps VBR | 128 kbps VBR | N/A |
| `high` | 320 kbps CBR | 256 kbps VBR | N/A |
| `lossless` | N/A | N/A | Compression level 5 |

#### Conversion Behavior
1. **Check if conversion needed**: Compare file extension against `--convert-from` list
2. **Skip if not in list**: File used as-is (may copy if `--copy-into` specified)
3. **Convert if in list**:
   - Run ffmpeg with quality preset
   - Preserve metadata (artist, title, album, year, artwork if present)
   - Output to temp file first, then rename on success
   - Update database with new file path and extension
4. **Error handling**:
   - Log conversion errors with ffmpeg output
   - Skip track if conversion fails (don't link broken file)
   - Continue to next track unless `--strict`

#### ffmpeg Command Template
```bash
ffmpeg -i "<input>" \
  -map_metadata 0 \
  -id3v2_version 3 \
  -codec:a <codec> \
  <quality_flags> \
  -y "<output>"
```

### Database Operations

#### Fields to Update in DjmdContent Table
1. **FolderPath**: Set to absolute path of local file
   - Normalized to NFC (macOS unicode normalization)
   - Canonical absolute path (symlinks resolved)
   
2. **FileSize**: Set to `os.path.getsize(file)` in bytes

3. **ServiceID**: Set to `0` (clears streaming flag)

4. **Provider Fields** (if present): Clear provider-specific metadata
   - `ProviderTrackID`
   - `ServiceMetadata`
   - Any other streaming-service fields

#### Pre-Update Validation
For each track:
1. **Find by ID**: Query `DjmdContent` by `rekordboxId`
   - If not found: Skip with reason "Track ID not found"
   
2. **Verify is streaming**: Check if track is actually a streaming track
   - FolderPath empty or contains service name, OR
   - ServiceID != 0
   - If already local and not `--force`: Skip with reason "Already local"

3. **Verify file exists**: Check that file path exists and is readable
   - If not found: Skip with reason "File not found"
   - If not readable: Skip with reason "Permission denied"

4. **Optional: Verify artist/title match**: Compare CSV to database
   - If mismatch and not `--allow-mismatch`: Skip with reason "Artist/title mismatch"
   - If mismatch and `--allow-mismatch`: Log warning and proceed

#### Transaction Handling
- Wrap all database updates in a single transaction
- If `--strict` and any error occurs: Rollback entire transaction
- If not `--strict`: Commit successful updates, log failed ones
- Verify affected row count = 1 for each update

### Fuzzy Matching Algorithm (with `--no-id-match`)

When using `--no-id-match`, tracks are matched based on artist and title similarity instead of Rekordbox IDs. This uses the same approach as `bandcamp_wishlist_automator.py`.

#### Matching Strategy

1. **Query Construction**: Combine artist + title into a single search string
   ```python
   search_query = f"{artist} {title}".lower()
   ```

2. **Database Scan**: Query all streaming tracks from Rekordbox database
   ```python
   streaming_tracks = get_all_streaming_tracks()
   ```

3. **Similarity Scoring**: For each database track, calculate combined similarity
   ```python
   db_query = f"{db_track.artist} {db_track.title}".lower()
   
   # Text cleaning (same as file_path_matcher.py)
   csv_clean = clean_text(search_query)  # Remove parens, brackets, special chars
   db_clean = clean_text(db_query)
   
   # Calculate similarity scores
   sequence_sim = SequenceMatcher(None, csv_clean, db_clean).ratio()
   word_sim = calculate_word_overlap(csv_clean, db_clean)
   
   # Combined score (weighted)
   similarity = (sequence_sim * 0.7) + (word_sim * 0.3)
   ```

4. **Best Match Selection**: Find track with highest similarity above threshold
   ```python
   if similarity >= match_threshold:  # Default 0.75
       best_match = db_track
   ```

5. **Validation**: Verify match is reasonable
   - Log match confidence score
   - If multiple tracks score similarly (within 0.05), log ambiguity warning
   - Proceed with best match unless ambiguous

#### Similarity Components

**Sequence Matching** (70% weight):
- Character-by-character comparison using Python's `difflib.SequenceMatcher`
- Handles typos, truncation, minor variations
- Example: "Leod - Untitled 05" vs "Leod Untitled 5" → ~0.85

**Word Overlap** (30% weight):
- Jaccard similarity of word sets
- `overlap = len(words_csv ∩ words_db) / len(words_csv ∪ words_db)`
- Handles word order differences, missing words
- Example: "Artist Track (Remix)" vs "Track Artist" → 0.67

#### Text Cleaning (borrowed from file_path_matcher.py)

```python
def clean_text(text: str) -> str:
    """Clean text for matching."""
    # Remove content in parentheses and brackets
    text = re.sub(r'\([^)]*\)', '', text)
    text = re.sub(r'\[[^\]]*\]', '', text)
    
    # Remove special characters
    text = re.sub(r'[^\w\s]', '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text.lower()
```

#### Match Quality Indicators

| Confidence | Similarity Score | Description |
|------------|------------------|-------------|
| **High** | ≥ 0.90 | Exact or near-exact match |
| **Good** | 0.75 - 0.89 | Strong match (default threshold) |
| **Medium** | 0.60 - 0.74 | Acceptable match (use with `--match-threshold 0.6`) |
| **Low** | < 0.60 | Rejected (likely wrong track) |

#### Ambiguity Handling

If multiple tracks score similarly (difference < 0.05):

```
⚠ Ambiguous match for "Artist - Track"
  Candidates:
    1. Artist - Track (Original Mix) [0.87]
    2. Artist - Track (Extended) [0.85]
  → Selected: #1 (highest score)
  → Use --strict to skip ambiguous matches
```

#### Example Matching Scenarios

**Scenario 1: Perfect Match**
```
CSV:      KVLR - 6am
Database: KVLR - 6am
Score:    0.98 (High confidence)
→ Match ✓
```

**Scenario 2: Remix Info Difference**
```
CSV:      Leod - Untitled 05
Database: Leod - Untitled 05 (Original Mix)
Score:    0.82 (Good confidence)
→ Match ✓
```

**Scenario 3: Artist Name Variation**
```
CSV:      Daft Punk - One More Time
Database: DAFT PUNK - One More Time
Score:    0.91 (High confidence)
→ Match ✓
```

**Scenario 4: Low Similarity**
```
CSV:      Artist A - Track 1
Database: Artist B - Track 2
Score:    0.35 (Low confidence)
→ No match ✗
```

**Scenario 5: Ambiguous**
```
CSV:      Artist - Track
DB #1:    Artist - Track (Original Mix) [0.85]
DB #2:    Artist - Track (Radio Edit) [0.84]
→ Match DB #1 with warning ⚠
```

#### Performance Considerations

- **First run**: Must scan all streaming tracks (~O(n) where n = streaming tracks)
- **Subsequent rows**: Results can be cached if scanning same database
- **Large libraries**: Consider `--limit` for testing before full run
- **Typical performance**: ~100-200ms per CSV row (including similarity calculations)

#### Safety Mechanisms

1. **Confidence logging**: All matches logged with similarity scores
2. **Ambiguity warnings**: Multiple close matches are flagged
3. **Dry-run preview**: See all matches before applying
4. **Report generation**: Review all fuzzy matches in detail
5. **Streaming-only matching**: Only considers streaming tracks (won't match local tracks)

### File Operations

#### Path Normalization
1. Expand user home (`~`) to absolute path
2. Resolve relative paths to absolute
3. Normalize to NFC unicode (macOS)
4. Resolve symlinks to canonical path
5. Validate file exists and is readable

#### Copy/Conversion Workflow (when `--copy-into` specified)
1. **Determine output path**:
   ```
   <copy-into>/<SanitizedArtist>/<SanitizedArtist> - <SanitizedTitle>.<ext>
   ```
   - Sanitize: Remove/replace `/ \ : * ? " < > |`
   - Handle duplicates: Append `(1)`, `(2)`, etc. if file exists

2. **Create directory structure**: `mkdir -p <artist_dir>`

3. **Convert or copy**:
   - If extension in `--convert-from`: Convert to target format
   - Else: Copy file as-is
   - Verify output file exists and size > 0

4. **Update database**: Use output path (not input path)

5. **Optional move**: If `--move`, delete original file after success

### Output and Reporting

#### Console Output

**With ID matching (default)**:
```
Rekordbox Link Local Files
===========================
CSV: matched_tracks.csv
Mode: DRY RUN (use --apply to execute)
Conversion: flac,wav → mp3 (high quality)
Library: ~/Music/Rekordbox-Library

Database backup created: master.db.backup.20250104_102030

Processing 117 tracks...
[1/117] ✓ Leod - Untitled 05
        Convert: /Music/Leod.flac → ~/Library/Leod/Leod - Untitled 05.mp3
[2/117] ✓ KVLR - 6am
        Copy: /Music/KVLR.wav → ~/Library/KVLR/KVLR - 6am.wav
[3/117] ⊘ Artist Name - Track Name
        Skipped: Already local
[4/117] ✗ Bad Track - Missing File
        Error: File not found at /Music/missing.flac

Summary
-------
Total tracks: 117
Updated: 85
Skipped: 25
  - Already local: 20
  - File not found: 3
  - Artist mismatch: 2
Errors: 7

Database updates: NOT APPLIED (dry-run)
Use --apply to execute changes.
```

**With fuzzy matching (`--no-id-match`)**:
```
Rekordbox Link Local Files
===========================
CSV: matched_tracks_no_ids.csv
Mode: DRY RUN (use --apply to execute)
Matching: Fuzzy (artist+title, threshold=0.75)
Conversion: flac,wav → mp3 (high quality)
Library: ~/Music/Rekordbox-Library

Database backup created: master.db.backup.20250104_102030
Loaded 1,234 streaming tracks from database

Processing 117 tracks...
[1/117] ✓ Leod - Untitled 05
        Matched: Leod - Untitled 05 (ID: 130248411) [confidence: 0.98]
        Convert: /Music/Leod.flac → ~/Library/Leod/Leod - Untitled 05.mp3
[2/117] ✓ KVLR - 6am
        Matched: KVLR - 6AM (ID: 181447005) [confidence: 0.89]
        Copy: /Music/KVLR.wav → ~/Library/KVLR/KVLR - 6am.wav
[3/117] ⚠ Artist - Track Name
        Matched: Artist - Track Name (Original Mix) (ID: 456789) [confidence: 0.79]
        Ambiguous: 2 similar matches found
        Copy: /Music/Artist.mp3 → ~/Library/Artist/Artist - Track Name.mp3
[4/117] ⊘ Unknown Artist - Missing Track
        Skipped: No match found (best: 0.42, threshold: 0.75)

Summary
-------
Total tracks: 117
Updated: 85
  - High confidence (≥0.90): 62
  - Good confidence (0.75-0.89): 20
  - Medium confidence (0.60-0.74): 3 (with --match-threshold 0.6)
Skipped: 25
  - No match found: 18
  - Already local: 5
  - File not found: 2
Ambiguous matches: 7
Errors: 7

Database updates: NOT APPLIED (dry-run)
Use --apply to execute changes.
```

#### Markdown Report (when `--report` specified)
```markdown
# Rekordbox Link Local Files Report
Generated: 2025-01-04 10:20:30

## Configuration
- **CSV**: matched_tracks.csv
- **Mode**: Applied changes
- **Conversion**: flac,wav → mp3 (high quality)
- **Library**: ~/Music/Rekordbox-Library
- **Database**: ~/Library/Pioneer/rekordbox/master.db
- **Backup**: master.db.backup.20250104_102030

## Summary
- **Total tracks**: 117
- **Successfully updated**: 85
- **Skipped**: 25
- **Errors**: 7

## Successfully Updated Tracks

### 1. Leod - Untitled 05
- **Rekordbox ID**: 130248411
- **Original**: Streaming (Beatport)
- **Conversion**: /Music/Leod.flac → mp3
- **New Path**: ~/Library/Leod/Leod - Untitled 05.mp3
- **Size**: 8.2 MB

### 2. KVLR - 6am
- **Rekordbox ID**: 181447005
- **Original**: Streaming (Tidal)
- **Action**: Copy (no conversion needed)
- **New Path**: ~/Library/KVLR/KVLR - 6am.wav
- **Size**: 42.1 MB

## Skipped Tracks

### Already Local (20 tracks)
1. Artist - Track (ID: 123456) - Already references local file

### File Not Found (3 tracks)
1. Artist - Missing Track (ID: 789012) - /Music/missing.flac

### Artist/Title Mismatch (2 tracks)
1. CSV: Artist A - Title | DB: Artist B - Title (ID: 345678)

## Errors

### Conversion Failed (7 tracks)
1. Artist - Track (ID: 901234)
   - Error: ffmpeg exited with code 1
   - Input: /Music/corrupt.flac
   - Output: Corrupt audio stream

## Recommendations
- Review error logs above for failed conversions
- Verify file paths for "File not found" errors
- Re-run with --allow-mismatch if artist mismatches are acceptable
```

### Error Handling

#### Error Categories
1. **CSV Errors**:
   - Missing required columns
   - Invalid track IDs (not integers)
   - Malformed CSV

2. **Database Errors**:
   - Cannot connect (Rekordbox running, permissions)
   - Track ID not found
   - Update failed (SQL error)

3. **File Errors**:
   - File not found
   - Permission denied
   - Invalid audio file
   - Conversion failed

4. **Validation Errors**:
   - Artist/title mismatch
   - Already local track
   - Unsupported format

#### Error Response Strategy
- **CSV errors**: Abort before processing (invalid input)
- **Database errors**: 
  - Connection: Abort with clear instructions
  - Track-specific: Skip track, continue (unless `--strict`)
- **File errors**: Skip track, log detailed error
- **Validation errors**: Skip track with reason

---

## Implementation Steps

### Phase 1: Foundation (1-2 days)

#### 1.1 Create CLI Module
**File**: `src/cli/link_local_command.py`

```python
import click
from pathlib import Path
from typing import List, Optional, Tuple
import csv
import os

@click.command(name="link-local")
@click.option("--csv", "csv_path", required=True, type=click.Path(exists=True),
              help="CSV file with rekordboxId, artist, song title, file path")
@click.option("--convert-from", "convert_from", type=str, default=None,
              help="Comma-separated list of formats to convert (e.g., flac,wav)")
@click.option("--convert-to", "convert_to", type=str, default=None,
              help="Target format for conversion (e.g., mp3)")
@click.option("--conversion-quality", "quality", 
              type=click.Choice(["low", "medium", "high", "lossless"]),
              default="high", help="Conversion quality preset")
@click.option("--copy-into", "copy_dir", type=click.Path(), default=None,
              help="Copy/convert files into managed library directory")
@click.option("--move", is_flag=True, default=False,
              help="Move files instead of copying (requires --copy-into)")
@click.option("--dry-run", is_flag=True, default=True,
              help="Preview changes without executing (default)")
@click.option("--apply", is_flag=True, default=False,
              help="Execute changes (disables dry-run)")
@click.option("--backup-db/--no-backup-db", default=True,
              help="Backup database before changes")
@click.option("--report", "report_path", type=click.Path(), default=None,
              help="Write detailed Markdown report")
@click.option("--strict", is_flag=True, default=False,
              help="Fail entire operation on first error")
@click.option("--limit", type=int, default=None,
              help="Process only first N rows")
@click.option("--db-path", type=click.Path(), default=None,
              help="Explicit path to Rekordbox database")
@click.option("--allow-mismatch", is_flag=True, default=False,
              help="Proceed even if artist/title don't match")
@click.option("--force", is_flag=True, default=False,
              help="Update tracks even if already local")
@click.option("--no-id-match", is_flag=True, default=False,
              help="Use fuzzy artist/title matching instead of IDs")
@click.option("--match-threshold", type=float, default=0.75,
              help="Similarity threshold for fuzzy matching (0.0-1.0)")
def link_local(**kwargs):
    """Convert streaming tracks to local file references."""
    # Implementation in following steps
    pass
```

**Tasks**:
- Create command structure with all options
- Add to `src/cli/__main__.py` entry point
- Wire into `setup.py` console_scripts

**Tests**:
- `tests/cli/test_link_local_command.py`: Test CLI argument parsing

#### 1.2 CSV Parsing Utilities
**File**: `src/lib/csv_parser.py`

```python
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
        """Parse CSV and return validated track mappings."""
        pass
    
    def validate_headers(self, headers: List[str]) -> Dict[str, str]:
        """Map flexible headers to canonical field names.
        
        Raises ValueError if required columns missing.
        """
        pass
    
    def normalize_path(self, path: str) -> Path:
        """Normalize file path (expand ~, resolve, NFC)."""
        pass
```

**Tasks**:
- Implement flexible column name matching
- Path normalization (expanduser, absolute, NFC unicode)
- File existence and size validation
- Handle BOM, different encodings

**Tests**:
- `tests/lib/test_csv_parser.py`: Various CSV formats, header variants

#### 1.3 Path Utilities
**File**: `src/lib/path_utils.py`

```python
def normalize_path(path: str) -> Path:
    """Normalize path for Rekordbox compatibility."""
    pass

def sanitize_filename(name: str) -> str:
    """Remove invalid filename characters."""
    pass

def build_library_path(copy_dir: Path, artist: str, title: str, ext: str) -> Path:
    """Build organized library path: <dir>/<artist>/<artist> - <title>.<ext>"""
    pass

def handle_duplicate_filename(path: Path) -> Path:
    """Add (1), (2), etc. if file exists."""
    pass
```

**Tests**:
- `tests/lib/test_path_utils.py`: Unicode, special chars, duplicates

#### 1.4 Fuzzy Matching Utilities
**File**: `src/lib/fuzzy_matcher.py`

```python
from difflib import SequenceMatcher
from typing import List, Tuple, Optional
import re

@dataclass
class MatchCandidate:
    """Represents a potential match from database."""
    track_id: int
    artist: str
    title: str
    similarity: float

class FuzzyMatcher:
    """Match tracks using artist+title similarity."""
    
    def __init__(self, threshold: float = 0.75):
        self.threshold = threshold
    
    def clean_text(self, text: str) -> str:
        """Clean text for matching (same as file_path_matcher.py)."""
        # Remove parentheses and brackets content
        text = re.sub(r'\([^)]*\)', '', text)
        text = re.sub(r'\[[^\]]*\]', '', text)
        
        # Remove special characters
        text = re.sub(r'[^\w\s]', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text.lower()
    
    def calculate_similarity(
        self,
        csv_artist: str,
        csv_title: str,
        db_artist: str,
        db_title: str
    ) -> float:
        """Calculate combined similarity score."""
        # Combine artist + title for both
        csv_query = self.clean_text(f"{csv_artist} {csv_title}")
        db_query = self.clean_text(f"{db_artist} {db_title}")
        
        # Sequence similarity (70% weight)
        sequence_sim = SequenceMatcher(None, csv_query, db_query).ratio()
        
        # Word overlap similarity (30% weight)
        csv_words = set(csv_query.split())
        db_words = set(db_query.split())
        
        if csv_words and db_words:
            intersection = len(csv_words.intersection(db_words))
            union = len(csv_words.union(db_words))
            word_sim = intersection / union if union > 0 else 0.0
        else:
            word_sim = 0.0
        
        # Combined score
        return (sequence_sim * 0.7) + (word_sim * 0.3)
    
    def find_best_match(
        self,
        csv_artist: str,
        csv_title: str,
        db_tracks: List[Track]
    ) -> Optional[MatchCandidate]:
        """Find best matching track from database.
        
        Returns:
            MatchCandidate if found, None otherwise
        """
        candidates = []
        
        for track in db_tracks:
            similarity = self.calculate_similarity(
                csv_artist, csv_title,
                track.artist or '', track.title or ''
            )
            
            if similarity >= self.threshold:
                candidates.append(MatchCandidate(
                    track_id=track.id,
                    artist=track.artist or '',
                    title=track.title or '',
                    similarity=similarity
                ))
        
        if not candidates:
            return None
        
        # Sort by similarity (descending)
        candidates.sort(key=lambda c: c.similarity, reverse=True)
        
        # Check for ambiguity (multiple close matches)
        best = candidates[0]
        if len(candidates) > 1:
            second_best = candidates[1]
            if best.similarity - second_best.similarity < 0.05:
                # Ambiguous match
                best.ambiguous = True
        
        return best
```

**Tasks**:
- Implement text cleaning (reuse logic from file_path_matcher.py)
- Implement similarity scoring (sequence + word overlap)
- Handle ambiguity detection
- Optimize for performance (consider caching)

**Tests**:
- `tests/lib/test_fuzzy_matcher.py`: Various match scenarios, edge cases

### Phase 2: Audio Conversion (2-3 days)

#### 2.1 Audio Converter Service
**File**: `src/services/audio_converter.py`

```python
@dataclass
class ConversionConfig:
    """Audio conversion configuration."""
    source_formats: List[str]  # e.g., ['flac', 'wav']
    target_format: str  # e.g., 'mp3'
    quality_preset: str  # 'low', 'medium', 'high', 'lossless'

@dataclass
class ConversionResult:
    """Result of audio conversion."""
    success: bool
    input_path: Path
    output_path: Optional[Path]
    duration_seconds: float
    error_message: Optional[str] = None

class AudioConverter:
    """Handle audio file conversion using ffmpeg."""
    
    QUALITY_PRESETS = {
        'mp3': {
            'low': ['-b:a', '128k'],
            'medium': ['-q:a', '2'],  # VBR ~190kbps
            'high': ['-b:a', '320k'],
        },
        'aac': {
            'low': ['-q:a', '0.3'],
            'medium': ['-q:a', '0.5'],
            'high': ['-q:a', '0.8'],
        },
        'flac': {
            'lossless': ['-compression_level', '5']
        }
    }
    
    def __init__(self, config: ConversionConfig):
        self.config = config
        self._verify_ffmpeg()
    
    def should_convert(self, file_path: Path) -> bool:
        """Check if file extension is in source formats list."""
        pass
    
    def convert(self, input_path: Path, output_path: Path) -> ConversionResult:
        """Convert audio file, preserving metadata."""
        pass
    
    def _build_ffmpeg_command(self, input: Path, output: Path) -> List[str]:
        """Build ffmpeg command with quality preset."""
        pass
    
    def _verify_ffmpeg(self):
        """Verify ffmpeg is installed and accessible."""
        pass
```

**Tasks**:
- Implement ffmpeg wrapper
- Quality preset mapping per codec
- Metadata preservation (ID3v2, Vorbis comments, MP4 tags)
- Temp file handling (atomic rename on success)
- Progress reporting (optional, via ffmpeg stderr parsing)

**Tests**:
- `tests/services/test_audio_converter.py`: Mock ffmpeg, test presets
- Integration test with real ffmpeg (optional, mark as slow)

#### 2.2 FFmpeg Integration
**Dependencies**: Add to `requirements.txt`:
```
ffmpeg-python>=0.2.0  # Optional: Python wrapper for ffmpeg
```

**Installation Check**: Command should verify ffmpeg is installed:
```python
import shutil
if not shutil.which('ffmpeg'):
    raise EnvironmentError("ffmpeg not found. Install with: brew install ffmpeg")
```

### Phase 3: Database Updates (2-3 days)

#### 3.1 Extend RekordboxAdapter
**File**: `src/services/rekordbox.py`

Add methods to existing `RekordboxAdapter` class:

```python
def get_track_by_id(self, track_id: int) -> Optional[Track]:
    """Fetch a single track by Rekordbox ID."""
    pass

def backup_database(self, backup_path: Optional[Path] = None) -> Path:
    """Create timestamped backup of database file."""
    pass

def update_track_to_local(
    self,
    track_id: int,
    file_path: Path,
    file_size: int
) -> bool:
    """Update a streaming track to reference a local file."""
    pass

def is_streaming_track(self, track_id: int) -> bool:
    """Check if track is currently a streaming track."""
    pass

def get_track_info(self, track_id: int) -> Tuple[str, str]:
    """Get artist and title for validation."""
    pass
```

**Implementation Details**:
```python
def update_track_to_local(self, track_id: int, file_path: Path, file_size: int) -> bool:
    """
    Update database to convert streaming track to local file.
    
    Fields updated in DjmdContent:
    - FolderPath: Set to absolute file path (NFC normalized)
    - FileSize: Set to actual file size in bytes
    - ServiceID: Set to 0 (clear streaming flag)
    - Provider fields: Clear if present
    
    Returns True if successful, False otherwise.
    """
    if not self.connected or self.db is None:
        return False
    
    try:
        # Check if pyrekordbox supports write operations
        if hasattr(self.db, 'update_content'):
            # Use library method if available
            return self._update_via_library(track_id, file_path, file_size)
        else:
            # Fallback to direct SQL update
            return self._update_via_sql(track_id, file_path, file_size)
    except Exception as e:
        self.error_message = f"Update failed: {str(e)}"
        return False

def _update_via_sql(self, track_id: int, file_path: Path, file_size: int) -> bool:
    """Direct SQL update (fallback if library doesn't support writes)."""
    # Access underlying SQLite connection
    # Use transaction for safety
    # UPDATE DjmdContent SET FolderPath=?, FileSize=?, ServiceID=0 WHERE ID=?
    pass
```

**Tasks**:
- Implement database backup (copy file with timestamp)
- Add get_track_by_id using existing pyrekordbox API
- Implement update methods (try library first, SQL fallback)
- Transaction handling and rollback support
- Row count verification

**Tests**:
- `tests/services/test_rekordbox_writes.py`: Mock database updates
- `tests/integration/test_db_updates.py`: With test database copy

#### 3.2 Transaction Manager
**File**: `src/services/db_transaction.py`

```python
class DatabaseTransaction:
    """Manage database transaction for batch updates."""
    
    def __init__(self, adapter: RekordboxAdapter, strict: bool = False):
        self.adapter = adapter
        self.strict = strict
        self.updates = []
        self.errors = []
    
    def add_update(self, track_id: int, file_path: Path, file_size: int):
        """Queue an update."""
        pass
    
    def execute(self) -> Tuple[int, int]:
        """Execute all queued updates. Returns (success_count, error_count)."""
        pass
    
    def rollback(self):
        """Rollback transaction on error (if strict mode)."""
        pass
```

### Phase 4: Main Orchestration (2 days)

#### 4.1 Link Local Service
**File**: `src/services/link_local_service.py`

```python
@dataclass
class LinkResult:
    """Result of linking a single track."""
    track_mapping: TrackMapping
    success: bool
    action: str  # 'updated', 'converted', 'copied', 'skipped'
    reason: Optional[str] = None  # Skip/error reason
    output_path: Optional[Path] = None
    conversion_result: Optional[ConversionResult] = None

class LinkLocalService:
    """Orchestrate the link-local operation."""
    
    def __init__(
        self,
        csv_path: Path,
        rekordbox_adapter: RekordboxAdapter,
        audio_converter: Optional[AudioConverter] = None,
        copy_dir: Optional[Path] = None,
        move: bool = False,
        dry_run: bool = True,
        strict: bool = False,
        limit: Optional[int] = None,
        allow_mismatch: bool = False,
        force: bool = False
    ):
        pass
    
    def execute(self) -> List[LinkResult]:
        """Execute the link-local operation."""
        # 1. Parse CSV
        # 2. Validate database connection
        # 3. Backup database if not dry-run
        # 4. Process each track:
        #    a. Validate track exists and is streaming
        #    b. Verify file exists
        #    c. Convert/copy if needed
        #    d. Update database
        # 5. Return results
        pass
    
    def _process_track(self, mapping: TrackMapping) -> LinkResult:
        """Process a single track mapping."""
        pass
    
    def _validate_track(self, mapping: TrackMapping) -> Tuple[bool, str]:
        """Validate track can be updated. Returns (valid, reason)."""
        pass
    
    def _handle_file(self, mapping: TrackMapping) -> Tuple[Path, int]:
        """Convert/copy file if needed. Returns (final_path, size)."""
        pass
```

#### 4.2 Report Generator
**File**: `src/services/report_generator.py`

```python
class LinkLocalReportGenerator:
    """Generate Markdown reports for link-local operations."""
    
    def generate(
        self,
        results: List[LinkResult],
        config: Dict,
        output_path: Path
    ):
        """Generate comprehensive Markdown report."""
        pass
    
    def _write_summary(self, results: List[LinkResult]) -> str:
        pass
    
    def _write_updated_tracks(self, results: List[LinkResult]) -> str:
        pass
    
    def _write_skipped_tracks(self, results: List[LinkResult]) -> str:
        pass
    
    def _write_errors(self, results: List[LinkResult]) -> str:
        pass
```

#### 4.3 Wire Up CLI Command
**File**: `src/cli/link_local_command.py` (complete implementation)

```python
def link_local(**kwargs):
    """Convert streaming tracks to local file references."""
    
    # 1. Validate arguments
    if kwargs['convert_to'] and not kwargs['convert_from']:
        raise click.UsageError("--convert-to requires --convert-from")
    
    if kwargs['move'] and not kwargs['copy_dir']:
        raise click.UsageError("--move requires --copy-into")
    
    dry_run = kwargs['dry_run'] and not kwargs['apply']
    
    # 2. Print configuration
    print("Rekordbox Link Local Files")
    print("=" * 50)
    print(f"CSV: {kwargs['csv_path']}")
    print(f"Mode: {'DRY RUN' if dry_run else 'APPLY CHANGES'}")
    
    if kwargs['convert_from']:
        print(f"Conversion: {kwargs['convert_from']} → {kwargs['convert_to']} "
              f"({kwargs['quality']})")
    
    if kwargs['copy_dir']:
        print(f"Library: {kwargs['copy_dir']}")
    
    print()
    
    # 3. Initialize services
    rekordbox = RekordboxAdapter()
    if not rekordbox.connect(kwargs['db_path']):
        click.echo(f"Error: {rekordbox.error_message}", err=True)
        sys.exit(1)
    
    converter = None
    if kwargs['convert_from']:
        config = ConversionConfig(
            source_formats=kwargs['convert_from'].split(','),
            target_format=kwargs['convert_to'],
            quality_preset=kwargs['quality']
        )
        converter = AudioConverter(config)
    
    # 4. Execute
    service = LinkLocalService(
        csv_path=Path(kwargs['csv_path']),
        rekordbox_adapter=rekordbox,
        audio_converter=converter,
        copy_dir=Path(kwargs['copy_dir']) if kwargs['copy_dir'] else None,
        move=kwargs['move'],
        dry_run=dry_run,
        strict=kwargs['strict'],
        limit=kwargs['limit'],
        allow_mismatch=kwargs['allow_mismatch'],
        force=kwargs['force']
    )
    
    try:
        results = service.execute()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        rekordbox.close()
    
    # 5. Print summary
    _print_summary(results, dry_run)
    
    # 6. Generate report if requested
    if kwargs['report_path']:
        generator = LinkLocalReportGenerator()
        generator.generate(results, kwargs, Path(kwargs['report_path']))
        print(f"\nDetailed report: {kwargs['report_path']}")
    
    # 7. Exit code based on errors
    error_count = sum(1 for r in results if not r.success and r.action != 'skipped')
    sys.exit(1 if error_count > 0 and kwargs['strict'] else 0)

def _print_summary(results: List[LinkResult], dry_run: bool):
    """Print console summary."""
    pass
```

### Phase 5: Testing & Documentation (1-2 days)

#### 5.1 Unit Tests
Create comprehensive tests for each module:

- `tests/lib/test_csv_parser.py`: CSV parsing, header flexibility
- `tests/lib/test_path_utils.py`: Path normalization, sanitization
- `tests/services/test_audio_converter.py`: Conversion logic (mocked ffmpeg)
- `tests/services/test_rekordbox_writes.py`: Database update methods
- `tests/services/test_link_local_service.py`: Main orchestration
- `tests/cli/test_link_local_command.py`: CLI argument handling

#### 5.2 Integration Tests
- `tests/integration/test_full_workflow.py`:
  - Test with sample CSV and test audio files
  - Use copy of real Rekordbox database (sanitized)
  - Verify database changes
  - Test dry-run vs apply
  - Test conversion pipeline

#### 5.3 Documentation Updates

**Update `WARP.md`**:
```markdown
### Link Local Files
```bash
# Link streaming tracks to local files (dry-run)
rekordbox link-local --csv matched_tracks.csv

# Apply with conversion
rekordbox link-local --csv matched_tracks.csv --apply \
  --convert-from flac,wav --convert-to mp3 \
  --copy-into ~/Music/Rekordbox-Library

# Generate detailed report
rekordbox link-local --csv matched_tracks.csv --apply \
  --report link_local_report.md
```

**Create `LINK_LOCAL_USAGE.md`**:
- Quick start guide
- Common workflows
- Troubleshooting
- FFmpeg installation instructions
- Example CSV files

#### 5.4 Error Message Catalog
Document all error messages and their resolutions:
- "Database is locked - please close Rekordbox"
- "ffmpeg not found - install with: brew install ffmpeg"
- "Track ID not found in database"
- etc.

### Phase 6: Polish & Safety (1 day)

#### 6.1 Safety Checklist
- [ ] Database always backed up before writes (unless --no-backup-db)
- [ ] Dry-run is default (require --apply to execute)
- [ ] Atomic file operations (temp files, rename on success)
- [ ] Transaction rollback on error (if --strict)
- [ ] Clear error messages with actionable advice
- [ ] Progress indication for long operations
- [ ] Ctrl+C handling (cleanup temp files, rollback transaction)

#### 6.2 Performance Optimization
- [ ] Batch database queries where possible
- [ ] Parallel audio conversion (optional, with --jobs N flag)
- [ ] Progress bar for large CSV files
- [ ] Efficient file copying (use shutil.copy2 for metadata)

#### 6.3 User Experience
- [ ] Clear, actionable error messages
- [ ] Color-coded console output (green success, yellow warning, red error)
- [ ] Estimated time remaining for conversions
- [ ] Confirmation prompt before destructive operations
- [ ] Help text with examples for each option

---

## Testing Strategy

### Test Database Setup
Create a sanitized test database with:
- 10 streaming tracks (various services: Tidal, Beatport, Spotify)
- 5 local tracks (to test skip logic)
- 3 tracks with various metadata edge cases

### Test Audio Files
Prepare sample files in:
- FLAC (lossless)
- WAV (lossless)
- MP3 (lossy)
- AAC (lossy)

Include:
- Valid audio with metadata
- Corrupt audio (test error handling)
- Zero-byte file (test validation)

### Manual Testing Checklist
- [ ] Dry-run shows correct preview
- [ ] Apply actually updates database
- [ ] Backup file created with timestamp
- [ ] Conversion preserves metadata
- [ ] Copy-into creates correct directory structure
- [ ] Duplicate filenames handled (adds (1), (2), etc.)
- [ ] Artist/title mismatch detected
- [ ] Already-local tracks skipped
- [ ] Ctrl+C cleanup works
- [ ] Report file generated correctly
- [ ] Rekordbox recognizes updated tracks (open GUI, verify local)

---

## Deployment Checklist

### Prerequisites
- [ ] Python >=3.9
- [ ] pyrekordbox >= 0.3.0
- [ ] ffmpeg installed (for conversion feature)
- [ ] Tested on macOS (primary platform)

### Installation
```bash
# Update dependencies
pip install -e .

# Verify command available
rekordbox link-local --help

# Install ffmpeg (if conversion needed)
brew install ffmpeg
```

### Release Notes Template
```markdown
## New Feature: Link Local Files

Convert streaming tracks in Rekordbox to local file references.

### Features
- CSV-driven track mapping
- Audio format conversion (FLAC, WAV → MP3, AAC, etc.)
- Managed library mode (copy/organize files)
- Safety first: dry-run by default, automatic backups
- Detailed reporting

### Usage
See LINK_LOCAL_USAGE.md for detailed documentation.

### Breaking Changes
None (new feature).

### Known Issues
- Requires Rekordbox to be closed
- Tracks may need re-analysis after conversion
```

---

## Future Enhancements

### Post-MVP Features
1. **Playlist Management**: Automatically create "Recently Linked" playlist
2. **Parallel Conversion**: Multi-threaded audio conversion (--jobs N)
3. **Smart Matching**: Fuzzy match CSV rows to DB if ID missing
4. **Rollback Command**: Revert a previous link-local operation
5. **Analysis Trigger**: AppleScript integration to trigger Rekordbox analysis
6. **Cloud Sync**: Option to upload converted files to cloud storage
7. **Batch Processing**: Process multiple CSV files in one run
8. **Web UI**: Simple web interface for non-technical users

### Optimization Opportunities
- Cache database queries (get_track_by_id results)
- Stream large CSV files instead of loading all into memory
- Incremental updates (only process changed rows)
- Resume interrupted conversions

---

## Risk Mitigation

### High-Priority Risks
1. **Database Corruption**
   - Mitigation: Mandatory backups, transaction rollback, thorough testing
   
2. **Data Loss (file operations)**
   - Mitigation: Copy by default, --move requires explicit flag, temp files

3. **Conversion Failures**
   - Mitigation: Validate before update, atomic operations, detailed error logs

### Medium-Priority Risks
1. **Performance (large libraries)**
   - Mitigation: Progress bars, --limit for testing, parallel conversion

2. **FFmpeg Availability**
   - Mitigation: Clear error message, installation instructions, skip conversion if not needed

3. **Path Compatibility (Windows/Linux)**
   - Mitigation: Use pathlib, test on multiple platforms, normalize unicode

---

## Success Criteria

### Functional Requirements Met
- [ ] Successfully converts streaming tracks to local in database
- [ ] Audio conversion works with quality presets
- [ ] Copy/move files into organized library structure
- [ ] Dry-run accurately previews changes
- [ ] Database backup created before changes
- [ ] Comprehensive error handling and reporting

### Quality Requirements Met
- [ ] >90% test coverage
- [ ] Zero database corruptions in testing
- [ ] Clear documentation with examples
- [ ] Conversion quality matches or exceeds source
- [ ] Performance acceptable (<1s per track excluding conversion)

### User Acceptance Criteria
- [ ] User can complete workflow without reading code
- [ ] Error messages actionable (user knows what to do)
- [ ] Dry-run gives confidence before applying
- [ ] Report provides audit trail of all changes
- [ ] Works with real-world messy data (flexible CSV, missing files, etc.)
