# Quickstart: Rekordbox Streaming Tag Exporter

**Purpose**: Step-by-step guide to validate the implementation works correctly.

## Prerequisites

1. **Python 3.11+** installed
2. **Rekordbox** installed with an existing music library
3. **Some streaming tracks** in your library (Beatport LINK, etc.)
4. **At least one tag** applied to some streaming tracks

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd rekordbox-tag-exporter

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

## Basic Usage

### Scenario 1: First Run (Interactive Mode)

```bash
# Run the command without arguments
rekordbox-export

# Expected flow:
# 1. Tool auto-detects your Rekordbox database
# 2. Displays list of tags with checkboxes
# 3. Use arrow keys to navigate, space to select, enter to confirm
# 4. Shows summary of tracks to export
# 5. Creates rekordbox_export.csv in current directory
```

**Validation**: 
- ✓ Check CSV file exists
- ✓ Open CSV in Excel/Numbers - verify Unicode characters display correctly
- ✓ First column contains track IDs (unique integers)
- ✓ Verify only streaming tracks are included
- ✓ Verify tracks have at least one of the selected tags

### Scenario 2: Custom Output Location

```bash
# Specify output file
rekordbox-export ~/Desktop/my_streaming_tracks.csv

# Select tags: "Deep House", "Techno"
```

**Validation**:
- ✓ File created at specified location
- ✓ Contains only tracks tagged with Deep House OR Techno
- ✓ All tracks are streaming (not local files)

### Scenario 3: Automated Export (No Interaction)

```bash
# Pre-select tags via command line
rekordbox-export --tags "House" "Techno" --overwrite output.csv

# No interaction required - direct export
```

**Validation**:
- ✓ No interactive prompts appear
- ✓ Export completes automatically
- ✓ Output matches tag criteria

## Error Scenarios

### Test 1: No Tags Selected

```bash
rekordbox-export
# When prompted for tags, press Enter without selecting any
```

**Expected**: Error message "At least one tag must be selected"

### Test 2: No Matching Tracks

```bash
rekordbox-export --tags "NonExistentTag"
```

**Expected**: Warning "No streaming tracks match selected tags"

### Test 3: Invalid Output Path

```bash
rekordbox-export /invalid/path/file.csv
```

**Expected**: Error "Cannot write to output file"

## Advanced Testing

### Performance Test

```bash
# Export with verbose output to see timing
rekordbox-export --verbose large_export.csv

# For very large libraries, test with limit
rekordbox-export --limit 1000 --verbose test.csv
```

**Validation**:
- ✓ Export completes within 10 seconds for 10k tracks
- ✓ Memory usage stays reasonable (< 500MB)

### Unicode Test

Create tags with special characters:
- 日本語 (Japanese)
- Россия (Russian)  
- 🎵🎶 (Emoji)

```bash
rekordbox-export --tags "日本語" unicode_test.csv
```

**Validation**:
- ✓ Tags display correctly in selection menu
- ✓ CSV contains tracks with Unicode artist/title names
- ✓ Excel opens file without encoding errors

## Troubleshooting

### Database Not Found

If the tool can't find your Rekordbox database:

```bash
# Manually specify database location
rekordbox-export --database "/path/to/rekordbox/database.db"

# Common locations:
# macOS: ~/Library/Pioneer/rekordbox/database.db
# Windows: C:\Users\{user}\AppData\Roaming\Pioneer\rekordbox\database.db
```

### Permission Denied

```bash
# If you get permission errors, check:
ls -la ~/Library/Pioneer/rekordbox/  # Check read permissions
```

## Integration Test Suite

Run the full test suite to validate all scenarios:

```bash
# Run all tests
pytest tests/integration/test_export_workflow.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

Expected test results:
- ✓ test_interactive_tag_selection
- ✓ test_no_tags_selected_error
- ✓ test_streaming_filter
- ✓ test_csv_unicode_handling
- ✓ test_no_matching_tracks
- ✓ test_large_library_performance

## Success Criteria

The implementation is considered successful when:

1. **Functional Requirements Met**:
   - [ ] Interactive tag selection works
   - [ ] Only streaming tracks exported
   - [ ] CSV contains track ID, artist, and title data
   - [ ] Track IDs are unique integers from Rekordbox database
   - [ ] At least one tag required validation works
   - [ ] No matches warning displayed correctly

2. **Performance Requirements Met**:
   - [ ] 10k tracks processed in < 10 seconds
   - [ ] Memory usage < 500MB for large libraries

3. **Quality Requirements Met**:
   - [ ] Unicode characters handled correctly
   - [ ] CSV opens in Excel without issues
   - [ ] All error scenarios handled gracefully

## Next Steps

After validation:
1. Review generated CSV for accuracy
2. Test with your specific DJ workflow
3. Report any issues or edge cases
4. Consider additional features (multiple output formats, etc.)