# Force Track Re-Analysis

## Overview

This feature allows you to force Rekordbox to re-analyze tracks by clearing their analysis data in the database. This is useful when:

- Beat grid detection was incorrect
- Waveform display is corrupted
- BPM detection needs to be recalculated
- You want Rekordbox to regenerate all analysis data

## How It Works

The tool clears the following fields in the `djmdContent` table:

| Field | What It Does |
|-------|-------------|
| `AnalysisDataPath` | Path to .DAT/.EXT analysis files |
| `Analysed` | Flag indicating if track has been analyzed (set to 0) |
| `SearchStr` | Cached search string (cleared) |
| `AnalysisUpdated` | Timestamp of last analysis (cleared) |

When these fields are cleared, Rekordbox will treat the track as if it has never been analyzed and will automatically re-analyze it when the track is loaded.

## Usage

### Using the Script

The simplest way to force re-analysis is using the provided script:

```bash
# Make sure Rekordbox is closed first!
python force_reanalyze_track.py <track_id>

# Example:
python force_reanalyze_track.py 53520270
```

### Using Python Code

You can also use the API directly:

```python
from src.services.rekordbox import RekordboxAdapter

# Connect to database
adapter = RekordboxAdapter()
adapter.connect()

# Backup first (recommended)
backup_path = adapter.backup_database()
print(f"Backup created: {backup_path}")

# Force re-analysis
track_id = 53520270
success = adapter.force_reanalyze(track_id)

if success:
    print("✓ Track will be re-analyzed when Rekordbox opens")
else:
    print(f"✗ Error: {adapter.error_message}")

adapter.close()
```

## Example Output

```
============================================================
Force Track Re-Analysis
============================================================
Track ID: 53520270

Connecting to Rekordbox database...
✓ Connected

Fetching track information...
✓ Found: Bontan, Josh Butler - Call You Back

Creating database backup...
✓ Backup created: master.backup.20251004_141130.db

Clearing analysis data to force re-analysis...
✓ Analysis data cleared successfully!

Next steps:
1. Open Rekordbox
2. Navigate to the track
3. Rekordbox should automatically re-analyze it
   (or you can manually trigger analysis)

The track should now have a fresh beat grid and waveform.
============================================================
```

## Verification

After running the script, you can verify the track's status:

```python
from src.services.rekordbox import RekordboxAdapter

adapter = RekordboxAdapter()
adapter.connect()

conn = adapter.db.engine.raw_connection()
cursor = conn.cursor()

cursor.execute('''
    SELECT Analysed, AnalysisDataPath 
    FROM djmdContent 
    WHERE ID = ?
''', (53520270,))

row = cursor.fetchone()
print(f"Analysed flag: {row[0]}")  # Should be 0
print(f"Analysis path: {row[1]}")  # Should be empty

adapter.close()
```

## What Happens Next

### When You Open Rekordbox:

1. **Automatic Re-Analysis**: Rekordbox will detect that the track has no analysis data
2. **Waveform Regeneration**: The waveform display will be regenerated
3. **Beat Grid Detection**: BPM and beat grid will be recalculated
4. **Cue Points Preserved**: Your hot cues, memory cues, and loops are NOT affected

### Manual Trigger (Alternative):

If automatic analysis doesn't trigger, you can manually analyze:
1. Right-click the track in Rekordbox
2. Select "Analyze Track" or "Reanalyze"
3. Rekordbox will regenerate all analysis data

## Important Notes

### ⚠️ Safety First

1. **Close Rekordbox**: Always close Rekordbox before running this tool
2. **Automatic Backup**: The script automatically creates a database backup before making changes
3. **Backup Location**: Backups are saved as `master.backup.YYYYMMDD_HHMMSS.db` in the same directory as your database

### 📁 What Is Preserved

This operation **ONLY** clears analysis data. The following are **NOT** affected:

✅ **Preserved:**
- Track metadata (artist, title, album, etc.)
- Hot cues and memory cues
- Loops
- Comments
- Ratings
- Playlists
- Tags
- Color labels
- File path/location

❌ **Cleared (will be regenerated):**
- Waveform display
- Beat grid
- BPM detection
- Analysis cache

### 🔄 Batch Processing

To force re-analysis of multiple tracks, create a simple loop:

```python
from src.services.rekordbox import RekordboxAdapter

track_ids = [53520270, 92643272, 195129795]

adapter = RekordboxAdapter()
adapter.connect()

# Backup once
backup_path = adapter.backup_database()
print(f"Backup: {backup_path}")

# Process all tracks
for track_id in track_ids:
    track = adapter.get_track_by_id(track_id)
    if track:
        success = adapter.force_reanalyze(track_id)
        if success:
            print(f"✓ {track.artist} - {track.title}")
        else:
            print(f"✗ Failed: {adapter.error_message}")

adapter.close()
```

## Use Cases

### Use Case 1: Incorrect Beat Grid
**Problem**: The beat grid doesn't align with the actual beats in the track.

**Solution**:
```bash
python force_reanalyze_track.py 53520270
```
Rekordbox will recalculate the beat grid from scratch.

### Use Case 2: Wrong BPM Detection
**Problem**: BPM is detected as 87 but should be 174 (or vice versa).

**Solution**: Force re-analysis and Rekordbox will recalculate the BPM.

### Use Case 3: Corrupted Waveform
**Problem**: Waveform display shows errors or is blank.

**Solution**: Clearing analysis data forces waveform regeneration.

### Use Case 4: After Audio Editing
**Problem**: You edited the audio file outside of Rekordbox and want fresh analysis.

**Solution**: Force re-analysis to match the updated audio.

## Troubleshooting

### "Track ID not found"
- Verify the track ID is correct
- Make sure you're using the correct database
- Check that Rekordbox is closed

### "Database is locked"
- Close Rekordbox completely
- Check for background processes: `ps aux | grep Rekordbox`
- Wait a few seconds and try again

### "Update affected 0 rows"
- Track might not exist in database
- Database might be read-only
- Check file permissions on the database

### Re-Analysis Doesn't Trigger
If Rekordbox doesn't automatically re-analyze:
1. Right-click the track
2. Select "Analyze Track"
3. Or select multiple tracks and use "Analyze" from the menu

## Database Schema Reference

The `djmdContent` table analysis-related fields:

```sql
CREATE TABLE djmdContent (
    ...
    AnalysisDataPath VARCHAR(255),  -- Path to .DAT/.EXT files
    Analysed INTEGER,                -- 0 = not analyzed, 1 = analyzed
    SearchStr VARCHAR(255),          -- Cached search string
    AnalysisUpdated VARCHAR(255),    -- Last analysis timestamp
    ...
);
```

## API Reference

### `RekordboxAdapter.force_reanalyze(track_id: int) -> bool`

Forces Rekordbox to re-analyze a track by clearing its analysis data.

**Parameters:**
- `track_id` (int): The Rekordbox track ID

**Returns:**
- `bool`: True if successful, False otherwise

**Raises:**
- No exceptions (errors are stored in `adapter.error_message`)

**Example:**
```python
adapter = RekordboxAdapter()
adapter.connect()

if adapter.force_reanalyze(53520270):
    print("Success!")
else:
    print(f"Error: {adapter.error_message}")

adapter.close()
```

## Related Files

- `src/services/rekordbox.py` - Contains the `force_reanalyze()` method
- `force_reanalyze_track.py` - Command-line script for easy use
- Database backups: `~/Library/Pioneer/rekordbox/master.backup.*.db`

## Safety & Best Practices

1. ✅ **Always backup** - The script does this automatically
2. ✅ **Close Rekordbox** - Database must not be locked
3. ✅ **Test on one track** - Before batch processing
4. ✅ **Verify results** - Check the track in Rekordbox after re-analysis
5. ⚠️ **Don't delete manually** - Use the provided tool instead of manual SQL

## Comparison with Manual Methods

| Method | Pros | Cons |
|--------|------|------|
| **This Tool** | Safe, automatic backup, precise | Requires Python |
| **Manual DB Edit** | Direct control | Risky, no backup, easy to break things |
| **Delete ANLZ Files** | Simple | Rekordbox might not detect the change |
| **Rekordbox UI** | Native, safe | Slow for many tracks, must do manually |

## Summary

The force re-analyze feature provides a safe, automated way to clear track analysis data and trigger Rekordbox to regenerate waveforms, beat grids, and BPM detection. It's particularly useful when analysis data is incorrect or corrupted, and you want Rekordbox to start fresh.

**Quick Start:**
```bash
# 1. Close Rekordbox
# 2. Run the script
python force_reanalyze_track.py 53520270
# 3. Open Rekordbox
# 4. Track will be automatically re-analyzed
```
