# Rekordbox Streaming Tag Exporter

Export streaming tracks from your Rekordbox library filtered by tags to CSV format.

## Features

- 🎵 Export streaming tracks from Rekordbox database
- 🏷️ Interactive tag selection from your Rekordbox database
- 🔍 Filter to only streaming service tracks (Beatport LINK, Tidal, etc.)
- 📊 Export to CSV with artist and title information
- 🌍 Full Unicode support for international tracks
- 🚀 Fast performance (<5 seconds for 10k tracks)
- 📈 Progress feedback during export

## Installation

### Prerequisites

- Python 3.11 or higher
- Rekordbox 6 installed (database will be auto-detected)

### Install from source

```bash
# Clone repository
git clone <repository-url>
cd specify-test

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

For development:
```bash
pip install -r requirements-dev.txt
```

## Usage

### Basic Usage

```bash
# Interactive tag selection
python -m src.cli rekordbox-export

# Or if installed:
rekordbox-export
```

### Command Options

```bash
rekordbox-export [OPTIONS]

Options:
  --db-path PATH     Path to Rekordbox database (auto-detected if not specified)
  -o, --output PATH  Output CSV file path (default: rekordbox_export.csv)
  --limit INTEGER    Limit number of tracks exported (for testing)
  --all-tags         Export all streaming tracks without tag filtering
  --tags TEXT        Specify tag names to filter (can be used multiple times)
  -q, --quiet        Suppress progress output
  --help             Show help message
```

### Examples

```bash
# Export all streaming tracks
rekordbox-export --all-tags

# Export with specific tags
rekordbox-export --tags "House" --tags "Techno" -o house_techno.csv

# Quick test with limit
rekordbox-export --all-tags --limit 100 -o test.csv

# Specify database path manually
rekordbox-export --db-path ~/Library/Pioneer/rekordbox/master.db
```

## CSV Output Format

The exported CSV contains:
- **id**: Track ID from Rekordbox database (for traceability)
- **artist**: Track artist name
- **title**: Track title  
- **streaming**: Whether it's a streaming track (Yes/No)

Files use UTF-8 with BOM encoding for Excel compatibility.

## Troubleshooting

### Database not found
```bash
# Specify database path manually
rekordbox-export --db-path /path/to/master.db
```

Common locations:
- macOS: `~/Library/Pioneer/rekordbox/master.db`
- Windows: `%APPDATA%\Pioneer\rekordbox\master.db`
- Linux: `~/.Pioneer/rekordbox/master.db`

### Database is locked
Close Rekordbox before running the export.

### No streaming tracks found
Ensure you have streaming tracks (Beatport LINK, Tidal, etc.) in your library.

## Development

This project follows Test-First Development (TDD) principles. All tests must be written and fail before implementation.

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
ruff check .
black .
mypy src/
```

## License

MIT
