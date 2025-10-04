# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a Python-based tool for exporting Rekordbox streaming tracks filtered by tags to CSV format. It consists of two main components:

1. **Rekordbox Library Export Tool** - Core functionality for extracting track data from Rekordbox databases
2. **Bandcamp Wishlist Automator** - Web automation for batch-processing tracks on Bandcamp

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Install in development mode
pip install -e .
```

### Running the Application
```bash
# Interactive tag selection (main CLI)
python -m src.cli

# Or if installed as package
rekordbox

# Export all streaming tracks
rekordbox --all-tags

# Export with specific tags
rekordbox --tags "House" --tags "Techno"

# Quick test with limited results
rekordbox --all-tags --limit 100
```

### Testing
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src

# Run specific test categories
pytest tests/integration/    # Integration tests
pytest tests/contract/       # Contract tests
pytest tests/cli/           # CLI tests
```

### Code Quality
```bash
# Format code
black .

# Lint code
ruff check .

# Type checking
mypy src/

# Pre-commit hooks (if installed)
pre-commit run --all-files
```

### Bandcamp Automator Setup
```bash
# Install Selenium dependency
pip install -r requirements_bandcamp.txt

# Install ChromeDriver (macOS)
brew install chromedriver

# Run bandcamp automator
python3 bandcamp_wishlist_automator.py

# Or use the batch processing script
./warp_bandcamp_batches.sh -i "Hard Groove.csv"
```

### File Path Matcher
```bash
# Match CSV tracks with local music files
python3 file_path_matcher.py --input "Hard Groove.csv" --scan-dir "~/Music" --output "matched_tracks.csv"

# With custom similarity threshold
python3 file_path_matcher.py -i tracks.csv -s /path/to/music -o results.csv --similarity 0.7

# Generate detailed report with confidence scores
python3 file_path_matcher.py -i tracks.csv -s ~/Music -o results.csv --report-path "match_report.md"

# Quick test with sample data
python3 file_path_matcher.py -i test_tracks.csv -s test_music -o test_results.csv
```

### Link Local Files
```bash
# Dry-run (preview changes) - ALWAYS DO THIS FIRST
python -m src.cli link-local --csv matched_tracks.csv

# Apply changes with ID matching
python -m src.cli link-local --csv matched_tracks.csv --apply

# Use fuzzy matching (no IDs required)
python -m src.cli link-local --csv tracks.csv --no-id-match --apply

# Test with limited rows first
python -m src.cli link-local --csv tracks.csv --apply --limit 5

# Lower threshold for more fuzzy matches
python -m src.cli link-local --csv tracks.csv --no-id-match --match-threshold 0.65 --apply

# Convert files to FLAC while linking (requires ffmpeg)
python -m src.cli link-local --csv tracks.csv --convert-to flac --apply

# Convert to WAV with custom output directory
python -m src.cli link-local --csv tracks.csv --convert-to wav --conversion-dir ~/Music/Converted --apply

# Convert only MP3 and AAC files to FLAC (filtering by source format)
python -m src.cli link-local --csv tracks.csv --convert-to flac --convert-from mp3 --convert-from aac --apply

# Convert to AIFF (Apple/Mac format)
python -m src.cli link-local --csv tracks.csv --convert-to aiff --apply

# Skip automatic re-analysis (keep existing beat grids)
python -m src.cli link-local --csv tracks.csv --apply --skip-reanalyze
```

## Architecture Overview

### Core Components

**Models (`src/models/`)**
- `Track` - Represents a music track with metadata and streaming detection
- `MyTag` - Represents Rekordbox user tags for filtering
- `TagSelection` - Handles tag selection logic
- `CSVExport` - Defines CSV output format

**Services (`src/services/`)**
- `RekordboxAdapter` - Database connection and query interface using pyrekordbox
- `CSVExporter` - Handles CSV file generation with proper encoding
- `TagSelector` - Interactive tag selection UI

**CLI (`src/cli/`)**
- Click-based command interface with automatic database detection
- Supports both interactive and non-interactive modes
- Auto-generates meaningful filenames based on selected tags

### Database Integration

The project uses `pyrekordbox` library to read Rekordbox 6 databases:

- **Auto-detection**: Finds database in standard locations (macOS, Windows, Linux)
- **Streaming detection**: Identifies streaming tracks by empty `FolderPath` or service names
- **Tag filtering**: Uses `MyTag` and `MyTagSongs` tables for track filtering
- **Error handling**: Detects locked databases and provides clear error messages

### Data Flow

1. **Connect** to Rekordbox database via `RekordboxAdapter`
2. **Load** available MyTags for user selection
3. **Filter** tracks by selected tags or get all streaming tracks
4. **Export** filtered tracks to CSV with UTF-8 BOM encoding for Excel compatibility
5. **Progress tracking** with real-time feedback

### Testing Strategy

The project follows Test-First Development (TDD):

- **Contract tests** - Verify external library interfaces (pyrekordbox)
- **Integration tests** - Full workflow testing with database connections
- **CLI tests** - Command-line interface validation
- **Error scenario tests** - Database locked, not found, etc.

### Bandcamp Automation

Separate automation system using Selenium WebDriver:

- **Batch processing** - Splits large CSV files into concurrent batches
- **Web automation** - Automated search, navigation, and wishlist management
- **Progress tracking** - Resumes interrupted sessions
- **Rate limiting** - Configurable delays to avoid overwhelming servers

### File Path Matcher

Standalone tool for matching CSV tracks with local music files:

- **Fuzzy matching** - Advanced similarity algorithms match track metadata with filenames
- **Recursive scanning** - Searches directories and subdirectories for music files
- **Format support** - Handles MP3, WAV, FLAC, AAC, M4A, OGG, WMA, AIFF, ALAC
- **Smart cleaning** - Removes parentheses, brackets, and filename artifacts for better matching
- **Configurable similarity** - Adjustable threshold for match precision vs recall
- **Detailed reporting** - Generates comprehensive Markdown reports with confidence scores and recommendations
- **Complete unmatched listing** - Shows full list of tracks that couldn't be matched

## Configuration

### Database Paths
- macOS: `~/Library/Pioneer/rekordbox/master.db`
- Windows: `%APPDATA%\Pioneer\rekordbox\master.db`
- Linux: `~/.Pioneer/rekordbox/master.db`

### CSV Output Format
- UTF-8 with BOM encoding for Excel compatibility
- Columns: id, artist, title, streaming (Yes/No)
- Auto-generated filenames based on tags and timestamp

### Key Dependencies
- `pyrekordbox>=0.3.0` - Rekordbox database access
- `click>=8.0` - CLI framework
- `selenium` - Web automation (bandcamp features)
- `pytest`, `black`, `ruff`, `mypy` - Development tools
- `ffmpeg` (optional) - Audio format conversion for link-local feature

## Important Notes

- Always close Rekordbox before running exports (database locking)
- The project maintains TDD discipline - write tests first
- Streaming track detection uses multiple heuristics (empty paths, service names)
- Tag IDs are stored as strings for database consistency
- Bandcamp automation requires manual login in browser first
- Audio conversion requires ffmpeg: `brew install ffmpeg` (macOS) or see https://ffmpeg.org/download.html
- Supported conversion formats: WAV, AIFF, FLAC, MP3 (320k), AAC (256k), ALAC
- Use `--convert-from` to selectively convert only specific source formats
