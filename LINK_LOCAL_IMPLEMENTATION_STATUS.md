# Link Local Files - Implementation Status

## ✅ Phase 1: Foundation (COMPLETED)

### Files Created:
1. **`src/lib/path_utils.py`** - Path normalization and filename handling
   - `normalize_path()` - NFC normalization for macOS compatibility
   - `sanitize_filename()` - Remove invalid characters
   - `build_library_path()` - Organized library structure
   - `handle_duplicate_filename()` - Collision handling

2. **`src/lib/fuzzy_matcher.py`** - Artist/title matching
   - `FuzzyMatcher` class with bandcamp-style matching
   - `clean_text()` - Remove parentheses, brackets, special chars
   - `calculate_similarity()` - 70% sequence + 30% word overlap
   - `find_best_match()` - Best match with ambiguity detection

3. **`src/lib/csv_parser.py`** - CSV parsing with flexible headers
   - `TrackMapping` dataclass with fuzzy matching fields
   - `CSVParser` with optional ID column support
   - Flexible column name matching (case-insensitive)
   - File validation and path normalization

## ⏳ Phase 2: Audio Conversion (NEEDED)

### To Implement:
- `src/services/audio_converter.py`
  - AudioConverter class with ffmpeg integration
  - Quality presets (low, medium, high, lossless)
  - Metadata preservation
  - Temp file handling

**Priority**: Medium (optional feature, can skip for MVP)

## 🔴 Phase 3: Database Operations (CRITICAL)

### To Implement:
- **Extend `src/services/rekordbox.py`** (CRITICAL):
  ```python
  def get_track_by_id(track_id: int) -> Optional[Track]
  def backup_database(backup_path: Optional[Path]) -> Path
  def update_track_to_local(track_id: int, file_path: Path, file_size: int) -> bool
  def is_streaming_track(track_id: int) -> bool
  ```

- **SQLite write support** (CRITICAL):
  - Access underlying SQLite connection
  - Transaction handling
  - UPDATE DjmdContent SET FolderPath=?, FileSize=?, ServiceID=0

## 🔴 Phase 4: Main Orchestration (CRITICAL)

### To Implement:
- `src/services/link_local_service.py` - Main business logic
  - LinkLocalService class
  - Process each track mapping
  - Validate, match, update workflow
  - Error handling and reporting

- `src/services/report_generator.py` - Markdown reports
  - LinkLocalReportGenerator class
  - Summary, matched tracks, unmatched tracks sections

## 🔴 Phase 5: CLI Integration (CRITICAL)

### To Implement:
- `src/cli/link_local_command.py` - Click command
  - All CLI options (--csv, --no-id-match, --match-threshold, etc.)
  - Argument validation
  - Service initialization
  - Progress output

- Wire into `src/cli/__main__.py`
- Update `setup.py` entry points

---

## Quick Start Guide (For Continuing Implementation)

### Next Steps (Priority Order):

1. **Database Operations** (CRITICAL - 2-3 hours)
   - Extend RekordboxAdapter with write methods
   - Test database backup
   - Test SQLite UPDATE operations

2. **CLI Command** (CRITICAL - 1-2 hours)
   - Create link_local_command.py
   - Wire into CLI entry point
   - Basic functionality without audio conversion

3. **LinkLocalService** (CRITICAL - 2-3 hours)
   - Main orchestration logic
   - ID-based matching first
   - Fuzzy matching second
   - File operations (copy/move)

4. **Report Generator** (Optional - 1 hour)
   - Can use simple console output for MVP
   - Markdown reports can be added later

5. **Audio Conversion** (Optional - 2-3 hours)
   - Can be skipped for MVP
   - Users can convert manually with ffmpeg
   - Add later if needed

### MVP Feature Set (Minimum Viable Product):

**Include**:
- ✅ CSV parsing with flexible headers
- ✅ Path utilities
- ✅ Fuzzy matching
- 🔴 Database writes (update FolderPath, FileSize, ServiceID)
- 🔴 CLI command with basic options
- 🔴 LinkLocalService (core logic)
- Dry-run mode
- Console output

**Skip for MVP**:
- Audio conversion (use existing files as-is)
- Markdown reports (console output sufficient)
- --copy-into (reference in place first)
- Advanced error recovery

### Testing Strategy:

1. **Manual Test with Sample Data**:
   ```bash
   # Create test CSV (3 tracks)
   # Run with --dry-run first
   rekordbox link-local --csv test.csv --dry-run
   
   # If looks good, apply
   rekordbox link-local --csv test.csv --apply --limit 1
   ```

2. **Database Backup Verification**:
   - Check backup file is created
   - Verify timestamp in filename
   - Compare file sizes

3. **Database Update Verification**:
   - Query track before and after
   - Check FolderPath changed
   - Check ServiceID = 0
   - Open Rekordbox GUI to verify

---

## File Structure Created:

```
src/
├── lib/
│   ├── path_utils.py          ✅ DONE
│   ├── fuzzy_matcher.py        ✅ DONE
│   └── csv_parser.py           ✅ DONE
├── services/
│   ├── rekordbox.py            ⏳ EXTEND (add write methods)
│   ├── audio_converter.py      ❌ TODO (optional)
│   └── link_local_service.py   ❌ TODO (critical)
└── cli/
    ├── link_local_command.py   ❌ TODO (critical)
    └── __main__.py             ⏳ EXTEND (wire in command)
```

---

## Usage Examples (Once Complete):

### Basic ID-based Matching:
```bash
# Dry-run (default)
rekordbox link-local --csv matched_tracks.csv

# Apply changes
rekordbox link-local --csv matched_tracks.csv --apply

# Test with limited rows
rekordbox link-local --csv matched_tracks.csv --apply --limit 5
```

### Fuzzy Matching (No IDs):
```bash
# Use fuzzy matching
rekordbox link-local --csv tracks_no_ids.csv --no-id-match --apply

# Adjust threshold
rekordbox link-local --csv tracks_no_ids.csv --no-id-match \
  --match-threshold 0.65 --apply
```

### With Conversion (Future):
```bash
rekordbox link-local --csv tracks.csv --apply \
  --convert-from flac,wav --convert-to mp3 \
  --copy-into ~/Music/Library
```

---

## Dependencies Check:

Already installed:
- ✅ click (CLI framework)
- ✅ pyrekordbox (database access)
- ✅ pathlib (standard library)
- ✅ difflib (standard library)

Needed for full implementation:
- ⚠️ ffmpeg (for audio conversion - optional)

---

## Risk Areas & Mitigation:

1. **Database Corruption** (HIGH RISK)
   - ✅ Mitigation: Always backup before writes
   - ✅ Mitigation: Use transactions
   - ✅ Mitigation: Test with copies first

2. **pyrekordbox Write Support** (MEDIUM RISK)
   - Issue: pyrekordbox may not expose write methods
   - ✅ Mitigation: Fall back to direct SQLite UPDATE
   - ✅ Mitigation: Access db._conn for raw SQL

3. **Path Compatibility** (LOW RISK)
   - ✅ Mitigation: NFC normalization implemented
   - ✅ Mitigation: Test with unicode filenames

4. **Fuzzy Matching Accuracy** (MEDIUM RISK)
   - ⚠️ Mitigation: Dry-run mode to preview matches
   - ⚠️ Mitigation: Adjustable threshold
   - ⚠️ Mitigation: Ambiguity warnings

---

## Estimated Time to Complete:

- **MVP** (ID matching, basic CLI, no conversion): 4-6 hours
- **Full Feature Set** (fuzzy matching, conversion, reports): 8-12 hours
- **Testing & Polish**: 2-4 hours

**Total Estimate**: 6-10 hours for MVP, 14-20 hours for complete feature

---

## Next Immediate Action:

**Start with Database Operations** - This is the most critical missing piece. Once database writes work, the rest can follow quickly.

Create `src/services/rekordbox.py` extensions with:
1. `backup_database()` method
2. `get_track_by_id()` method  
3. `update_track_to_local()` method with SQL fallback
