# DJ Tool Suite

A comprehensive toolset for managing your Rekordbox library and automating DJ workflows.

## Features

- 🎵 **Export streaming tracks** from Rekordbox database filtered by tags
- 🔗 **Link local files** to replace streaming tracks with optional audio format conversion
- 🎯 **Match CSV tracks** with local music files using advanced fuzzy matching
- 🎧 **Bandcamp automation** for batch wishlist additions
- 🏷️ Interactive tag selection from your Rekordbox database
- 🔍 Filter only streaming service tracks (Beatport LINK, Tidal, etc.)
- 📊 Export to CSV with artist and title information
- 🌍 Full Unicode support for international tracks
- 🚀 Fast performance (<5 seconds for 10k tracks)
- 📈 Progress feedback during all operations
- 🎛️ Audio conversion support (WAV, AIFF, FLAC, MP3, AAC, ALAC)

## Installation

### Prerequisites

- **Python 3.11 or higher** - Check with `python3 --version`
- **Rekordbox 6** installed (database will be auto-detected)
- **FFmpeg** (optional) - Required for audio conversion features
  - macOS: `brew install ffmpeg`
  - Other platforms: See [FFmpeg download page](https://ffmpeg.org/download.html)

### Quick Install

```bash
# Clone repository
git clone <repository-url>
cd dj-util

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install application
pip install -e .
```

### Development Setup

For development with testing and code quality tools:

```bash
# After basic installation above
pip install -r requirements-dev.txt

# Install pre-commit hooks (optional)
pre-commit install
```

### Verify Installation

```bash
# Test the installation
dj-tool --help

# Or using module syntax
python -m cli --help
```

## Usage

The DJ Tool Suite provides several commands for different workflows:

```bash
dj-tool [COMMAND] [OPTIONS]

# Available Commands:
#   rekordbox-export        Export streaming tracks from Rekordbox
#   rekordbox-link-local    Link local files to replace streaming tracks  
#   match-files             Match CSV tracks with local music files
#   bandcamp-wishlist-add   Automate Bandcamp wishlist additions
```

### 1. Export Rekordbox Streaming Tracks

Export streaming tracks from your Rekordbox database:

```bash
# Interactive tag selection
dj-tool rekordbox-export

# Export all streaming tracks
dj-tool rekordbox-export --all-tags

# Export specific tags
dj-tool rekordbox-export --tags "House" --tags "Techno" 

# Quick test with limit
dj-tool rekordbox-export --all-tags --limit 100

# Custom output file
dj-tool rekordbox-export --all-tags -o my_tracks.csv
```

### 2. Link Local Files (Replace Streaming Tracks)

Replace streaming tracks in Rekordbox with local music files:

```bash
# ALWAYS dry-run first to preview changes
dj-tool rekordbox-link-local --csv matched_tracks.csv

# Apply changes with ID matching
dj-tool rekordbox-link-local --csv matched_tracks.csv --apply

# Use fuzzy matching (no IDs required)
dj-tool rekordbox-link-local --csv tracks.csv --no-id-match --apply

# Convert files while linking (requires FFmpeg)
dj-tool rekordbox-link-local --csv tracks.csv --convert-to flac --apply

# Convert only specific formats
dj-tool rekordbox-link-local --csv tracks.csv --convert-to flac --convert-from mp3 --convert-from aac --apply

# Skip automatic track re-analysis
dj-tool rekordbox-link-local --csv tracks.csv --apply --skip-reanalyze
```

**Supported conversion formats:** WAV, AIFF, FLAC, MP3 (320k), AAC (256k), ALAC

### 3. Match Files with CSV Tracks

Find local music files that match tracks in your CSV:

```bash
# Match tracks with local files
dj-tool match-files --input "my_tracks.csv" --scan-dir "~/Music" --output "matched_tracks.csv"

# Custom similarity threshold
dj-tool match-files -i tracks.csv -s /path/to/music -o results.csv --similarity 0.7

# Generate detailed match report
dj-tool match-files -i tracks.csv -s ~/Music -o results.csv --report-path "match_report.md"
```

### 4. Bandcamp Wishlist Automation

Automate adding tracks to your Bandcamp wishlist:

```bash
# Add tracks from CSV to Bandcamp wishlist
dj-tool bandcamp-wishlist-add --csv-file "my_tracks.csv"

# Resume from specific track (useful if interrupted)
dj-tool bandcamp-wishlist-add --csv-file "tracks.csv" --start-from-row 150
```

## Complete Workflow Example

Here's a typical workflow using the DJ Tool Suite:

```bash
# 1. Export streaming tracks from Rekordbox
dj-tool rekordbox-export --tags "House" --tags "Techno" -o my_house_tracks.csv

# 2. Match tracks with local music files
dj-tool match-files -i my_house_tracks.csv -s ~/Music -o matched_tracks.csv --report-path match_report.md

# 3. Preview what will be linked (dry-run)
dj-tool rekordbox-link-local --csv matched_tracks.csv

# 4. Link local files and convert to FLAC
dj-tool rekordbox-link-local --csv matched_tracks.csv --convert-to flac --apply

# 5. (Optional) Add remaining unmatched tracks to Bandcamp wishlist
dj-tool bandcamp-wishlist-add --csv-file my_house_tracks.csv
```

### Auto-Generated Filenames

When no output file is specified, filenames are automatically generated:
- No tags: `rekordbox_export_YYYYMMDD_HHMMSS.csv`
- All tags: `rekordbox_all_streaming_YYYYMMDD_HHMMSS.csv`
- Specific tags: `rekordbox_house_techno_YYYYMMDD_HHMMSS.csv`
- Many tags: `rekordbox_house_techno_trance_and_more_YYYYMMDD_HHMMSS.csv`

## CSV Output Format

The exported CSV contains:
- **id**: Track ID from Rekordbox database (for traceability)
- **artist**: Track artist name
- **title**: Track title  
- **streaming**: Whether it's a streaming track (Yes/No)

Files use UTF-8 with BOM encoding for Excel compatibility.

## File Formats and Compatibility

### CSV Output Format
The exported CSV contains:
- **id**: Track ID from Rekordbox database (for traceability)
- **artist**: Track artist name
- **title**: Track title  
- **streaming**: Whether it's a streaming track (Yes/No)
- **file_path**: Local file path (when using match-files)

Files use UTF-8 with BOM encoding for Excel compatibility.

### Supported Audio Formats
**Input formats** (for matching and linking):
MP3, WAV, FLAC, AAC, M4A, OGG, WMA, AIFF, ALAC

**Output formats** (for conversion):
- **WAV**: Uncompressed, maximum compatibility
- **AIFF**: Apple's uncompressed format
- **FLAC**: Lossless compression, smaller file sizes
- **MP3**: 320kbps CBR for compatibility
- **AAC**: 256kbps for Apple ecosystem
- **ALAC**: Apple Lossless, smaller than AIFF

## Troubleshooting

### Common Issues

**"Database not found"**
```bash
# Specify database path manually
dj-tool rekordbox-export --db-path /path/to/master.db
```

Common Rekordbox database locations:
- **macOS**: `~/Library/Pioneer/rekordbox/master.db`
- **Windows**: `%APPDATA%\Pioneer\rekordbox\master.db`
- **Linux**: `~/.Pioneer/rekordbox/master.db`

**"Database is locked"**
- Close Rekordbox completely before running any commands
- Wait a few seconds after closing before trying again

**"No streaming tracks found"**
- Ensure you have streaming tracks (Beatport LINK, Tidal, etc.) in your library
- Check that tracks show as "streaming" in Rekordbox

**"FFmpeg not found" (during conversion)**
```bash
# Install FFmpeg
brew install ffmpeg  # macOS
# See https://ffmpeg.org/download.html for other platforms
```

**"Module not found" errors**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall in development mode
pip install -e .
```

### Getting Help

```bash
# Get help for main command
dj-tool --help

# Get help for specific commands
dj-tool rekordbox-export --help
dj-tool rekordbox-link-local --help
dj-tool match-files --help
dj-tool bandcamp-wishlist-add --help
```

## Development

This project follows Test-First Development (TDD) principles.

### Running Tests
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src

# Run specific test types
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

# Run all quality checks
pre-commit run --all-files  # If pre-commit is installed
```

### Project Structure
```
src/
├── cli/                 # Command-line interfaces
├── models/             # Data models (Track, Tag, etc.)
├── services/           # Business logic (RekordboxAdapter, CSVExporter)
└── utils/              # Utility functions

tests/
├── cli/                # CLI command tests
├── contract/           # External dependency tests
├── integration/        # Full workflow tests
└── unit/              # Unit tests
```

## License

MIT
