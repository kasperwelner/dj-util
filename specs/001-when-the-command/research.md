# Research & Technical Decisions

**Feature**: Rekordbox Streaming Tag Exporter  
**Date**: 2025-09-29  
**Phase**: 0 - Research & Discovery

## Executive Summary
Technical research for a CLI tool that exports Rekordbox streaming tracks filtered by tags to CSV format. Key decisions focus on pyrekordbox integration, interactive CLI design, and robust CSV handling.

## Important Data Model Corrections

**Based on pyrekordbox documentation review**:
- Rekordbox uses "MyTag" terminology, not just "Tag" (stored in DjmdMyTag table)
- MyTags do NOT have color attributes (this was incorrect in initial spec)
- Tracks are stored in DjmdContent table with specific field names:
  - FolderPath: Empty for streaming tracks (key identifier)
  - FilePath: Contains streaming URI for streaming tracks
  - Artist, Title: Track metadata fields
- Many-to-many relationship via ContentMyTag junction table

## Technical Decisions

### 1. Rekordbox Database Access
**Decision**: Use pyrekordbox library with adapter pattern  
**Rationale**: 
- Official Python library for Rekordbox database interaction
- Handles complex database format and version compatibility
- Provides typed models for tracks, tags, and metadata
- Active maintenance and community support

**Alternatives considered**:
- Direct SQLite access: Rejected - Rekordbox uses proprietary database format
- rekordbox-xml export parsing: Rejected - Requires manual export step, doesn't include all metadata
- Pioneer's WebAPI: Rejected - Requires Rekordbox running, not available for all versions

### 2. CLI Framework
**Decision**: Use click framework for CLI implementation  
**Rationale**:
- Mature, well-documented framework
- Built-in support for interactive prompts and checkboxes
- Excellent Unicode handling for international text
- Automatic help generation and argument parsing
- Easy testing with CliRunner

**Alternatives considered**:
- typer: Good alternative, but click has better interactive widget support
- argparse (stdlib): Rejected - Limited interactive UI capabilities
- Rich + questionary: Rejected - Additional dependencies for basic functionality

### 3. Interactive Tag Selection
**Decision**: Use click.Choice with multiple=True for checkbox behavior  
**Rationale**:
- Native click functionality, no extra dependencies
- Keyboard-friendly navigation (space to select, enter to confirm)
- Accessible for screen readers
- Works across all terminal types

**Alternatives considered**:
- inquirer: Rejected - Additional dependency, less maintained
- blessed/urwid: Rejected - Overly complex for simple checkbox list
- Simple numbered menu: Rejected - Poor UX for multiple selections

### 4. CSV Export Format
**Decision**: Use Python csv.DictWriter with UTF-8-sig encoding  
**Rationale**:
- UTF-8-sig adds BOM for Excel compatibility
- DictWriter provides clean column mapping
- Handles special characters and quotes automatically
- Standard library, no dependencies

**Alternatives considered**:
- pandas DataFrame.to_csv: Rejected - Heavy dependency for simple export
- Manual CSV string building: Rejected - Error-prone with escaping
- JSON export: Rejected - Not requested, less compatible with DJ tools

### 5. Streaming Track Detection
**Decision**: Check for empty FolderPath field (as clarified in spec)  
**Rationale**:
- Confirmed by user as reliable indicator
- Simple boolean check, no complex parsing
- Consistent across Rekordbox versions
- Fast filtering operation

**Alternatives considered**:
- URL scheme detection: Rejected - FolderPath method is simpler
- File existence check: Rejected - Slower, requires filesystem access
- Metadata flags: Rejected - Not consistently available

## Best Practices Implementation

### Error Handling
- Graceful database connection failures with clear messages
- Validate Rekordbox database exists before opening
- Handle corrupted/incompatible database versions
- Provide actionable error messages for DJ users

### Performance Optimization
- Lazy loading of tracks (generator pattern)
- Filter streaming tracks at query level if possible
- Stream CSV writing for large exports
- Progress indicator for long operations

### Testing Strategy
- Contract tests for pyrekordbox data structures
- Mock Rekordbox database for unit tests
- Integration tests with sample database fixtures
- CSV format validation tests
- Unicode handling test cases

### User Experience
- Clear progress feedback during export
- Confirmation before overwriting existing CSV files
- Summary statistics (X tracks exported from Y tags)
- Graceful cancellation (Ctrl+C) handling

## Implementation Risks & Mitigations

### Risk 1: Rekordbox Database Format Changes
**Mitigation**: 
- Pin pyrekordbox version in requirements
- Add version detection and compatibility warnings
- Contract tests to detect breaking changes early

### Risk 2: Large Library Performance
**Mitigation**:
- Implement streaming/chunked processing
- Add --limit flag for testing with subset
- Memory profiling in tests

### Risk 3: Character Encoding Issues
**Mitigation**:
- Comprehensive Unicode test suite
- UTF-8-sig for Excel compatibility
- Fallback encoding detection

## Dependencies Summary

### Required
- `pyrekordbox>=0.3.0` - Rekordbox database interaction
- `click>=8.0` - CLI framework
- `pytest>=7.0` - Testing framework

### Development
- `pytest-cov` - Coverage reporting
- `black` - Code formatting
- `ruff` - Linting
- `mypy` - Type checking

## Next Steps
1. Create data models based on pyrekordbox entities
2. Design CLI command interface contract
3. Write contract tests for database integration
4. Implement TDD workflow per constitution

## References
- [pyrekordbox documentation](https://pyrekordbox.readthedocs.io/)
- [Click documentation](https://click.palletsprojects.com/)
- [CSV format RFC 4180](https://tools.ietf.org/html/rfc4180)
- [Rekordbox database structure](https://github.com/Deep-Symmetry/crate-digger)