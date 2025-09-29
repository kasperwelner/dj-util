# Rekordbox Streaming Tag Exporter

Export streaming tracks from your Rekordbox library filtered by tags to CSV format.

## Features

- Interactive tag selection from your Rekordbox database
- Filter to only streaming service tracks (Beatport LINK, etc.)
- Export to CSV with track ID, artist, and title
- Full Unicode support for international tracks
- Progress feedback during export

## Installation

```bash
pip install -e .
```

For development:
```bash
pip install -r requirements-dev.txt
```

## Usage

```bash
rekordbox-export
```

## Development

This project follows Test-First Development (TDD) principles. All tests must be written and fail before implementation.

## License

MIT