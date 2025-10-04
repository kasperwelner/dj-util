# Automatic Re-Analysis in Link-Local

## Overview

The link-local command now **automatically marks tracks for re-analysis** when they are linked to local files. This ensures that Rekordbox regenerates waveforms, beat grids, and BPM detection for the newly linked audio files.

## Why This Matters

When you convert a streaming track to a local file:
- The audio file is different from what Rekordbox analyzed before
- Waveforms may need to be regenerated
- Beat grids should match the actual audio file
- BPM detection should be accurate for the local file

**Automatic re-analysis ensures everything stays synchronized!**

## How It Works

### Default Behavior (Re-Analysis Enabled)

By default, every successfully linked track is automatically marked for re-analysis:

```bash
# This will mark all linked tracks for re-analysis
python -m src.cli link-local --csv tracks.csv --apply
```

**Output:**
```
[1/5] → Bontan, Josh Butler - Call You Back
   ✓ Updated: /Users/you/Music/track.flac
   🔄 Marking for re-analysis...
   ✓ Will be re-analyzed when Rekordbox opens
```

### Skipping Re-Analysis

If you want to keep existing analysis data (waveforms, beat grids), use `--skip-reanalyze`:

```bash
# This will NOT mark tracks for re-analysis
python -m src.cli link-local --csv tracks.csv --apply --skip-reanalyze
```

**Output:**
```
[1/5] → Bontan, Josh Butler - Call You Back
   ✓ Updated: /Users/you/Music/track.flac
```

## When Re-Analysis Happens

### During Link-Local Execution:
1. Track is updated to reference local file ✅
2. Analysis data is cleared (Analysed = 0) ✅
3. Track is marked for re-analysis ✅

### When You Open Rekordbox:
1. Rekordbox detects tracks with no analysis
2. Automatically re-analyzes them in background
3. Generates fresh waveforms and beat grids
4. Detects BPM from actual audio

## What Gets Regenerated

When a track is re-analyzed, Rekordbox regenerates:

✅ **Regenerated:**
- Waveform display
- Beat grid alignment
- BPM detection
- Key detection (if enabled)
- Analysis cache files

❌ **Preserved (NOT affected):**
- Hot cues and memory cues
- Loops
- Comments
- Ratings
- Playlists
- Tags
- Color labels

## Use Cases

### Use Case 1: Format Conversion
**Scenario:** Converting streaming MP3s to lossless FLAC.

```bash
python -m src.cli link-local --csv tracks.csv --convert-to flac --apply
```

**Result:**
- Files converted to FLAC ✅
- Rekordbox updated to point to FLAC files ✅
- Tracks marked for re-analysis ✅
- Waveforms will match the FLAC audio ✅

---

### Use Case 2: Keeping Existing Analysis
**Scenario:** You already have perfect beat grids and don't want to lose them.

```bash
python -m src.cli link-local --csv tracks.csv --apply --skip-reanalyze
```

**Result:**
- Files linked ✅
- Existing analysis preserved ✅
- No waveform regeneration ❌

**⚠️ Warning:** If the audio file is different from what was analyzed, waveforms may not match!

---

### Use Case 3: Mixed Approach
**Scenario:** Some tracks need re-analysis, others don't.

```bash
# First batch: Tracks that need re-analysis
python -m src.cli link-local --csv new_tracks.csv --apply

# Second batch: Tracks with perfect analysis
python -m src.cli link-local --csv analyzed_tracks.csv --apply --skip-reanalyze
```

---

## Dry-Run Output

In dry-run mode, you'll see what would happen:

```bash
python -m src.cli link-local --csv tracks.csv
```

**Output:**
```
============================================================
Rekordbox Link Local Files
============================================================
CSV: tracks.csv
Mode: DRY RUN (preview only)
Matching: ID-based
Force re-analysis: Yes (tracks will be re-analyzed in Rekordbox)

[1/3] → Track Name
   → Would update: /path/to/file.flac
   → Would mark for re-analysis

Summary
-------
Total tracks: 3
Updated: 3
Skipped: 0
Errors: 0

Database updates: NOT APPLIED (dry-run)
```

With `--skip-reanalyze`:
```
Force re-analysis: No (skipped)

[1/3] → Track Name
   → Would update: /path/to/file.flac

(no re-analysis line)
```

## Summary Statistics

After running with `--apply`, the summary shows:

```
Summary
-------
Total tracks: 10
Updated: 10
Skipped: 0
Errors: 0
Marked for re-analysis: 10

Database updates: APPLIED
```

The "Marked for re-analysis" count shows how many tracks were successfully marked.

## Technical Details

### Database Changes

When re-analysis is enabled, these fields are cleared:

```sql
UPDATE djmdContent 
SET AnalysisDataPath = '',
    Analysed = 0,
    SearchStr = '',
    AnalysisUpdated = ''
WHERE ID = ?
```

### Process Flow

```
1. Read CSV
2. Find track in database
3. Validate file exists
4. [Optional] Convert audio format
5. Update track to local file  ← Database write #1
6. [Optional] Mark for re-analysis  ← Database write #2
7. Report success
```

### Error Handling

If re-analysis marking fails, the track is still successfully linked:

```
[1/1] → Track Name
   ✓ Updated: /path/to/file.flac
   🔄 Marking for re-analysis...
   ⚠ Could not mark for re-analysis: [error message]
```

The track is usable, but you'll need to manually trigger analysis in Rekordbox.

## Best Practices

### ✅ Recommended: Use Default (Re-Analysis Enabled)

For most use cases, **keep the default behavior**:
- Ensures waveforms match audio files
- Beat grids are accurate
- BPM detection is correct
- No manual work needed

### ⚠️ Use --skip-reanalyze Only When:

1. **You have perfect beat grids** that took hours to create
2. **The audio file is identical** to what was analyzed
3. **You want to manually trigger analysis** later
4. **You're testing** and don't want to wait for analysis

### 💡 Pro Tips

1. **Test with small batch first:**
   ```bash
   python -m src.cli link-local --csv tracks.csv --limit 5 --apply
   ```

2. **Use dry-run to preview:**
   ```bash
   python -m src.cli link-local --csv tracks.csv
   ```

3. **Monitor Rekordbox analysis:**
   - Open Rekordbox after linking
   - Watch the analysis queue in the bottom panel
   - Wait for all tracks to finish analyzing

4. **Backup before batch operations:**
   - Automatic backup is created ✅
   - But keep your own backup too!

## Comparison with Manual Methods

| Method | Speed | Accuracy | Manual Work |
|--------|-------|----------|-------------|
| **Auto Re-Analysis** | Fast | Automatic | None |
| **--skip-reanalyze** | Fastest | May be wrong | Manual fix needed |
| **Manual in Rekordbox** | Slow | User-controlled | Lots |

## FAQ

### Q: Will this delete my hot cues?
**A:** No! Hot cues, memory cues, and loops are completely preserved.

### Q: Can I cancel re-analysis after it starts?
**A:** Yes, but only in Rekordbox. The database changes have already been made.

### Q: What if I close Rekordbox during analysis?
**A:** Analysis will resume when you reopen Rekordbox.

### Q: Does this work with audio conversion?
**A:** Yes! Works perfectly with `--convert-to`:
```bash
python -m src.cli link-local --csv tracks.csv --convert-to flac --apply
```

### Q: How long does re-analysis take?
**A:** Typically 5-30 seconds per track in Rekordbox. Depends on:
- Audio file length
- Computer CPU speed
- Other Rekordbox operations

### Q: Can I batch process hundreds of tracks?
**A:** Yes! The link-local command is designed for batch operations:
```bash
python -m src.cli link-local --csv 500_tracks.csv --apply
```

### Q: What if some tracks fail to be marked?
**A:** The track is still successfully linked. You can:
1. Manually trigger analysis in Rekordbox
2. Or run force_reanalyze_track.py on specific tracks

## Related Commands

### Force Re-Analysis on Specific Track
```bash
python force_reanalyze_track.py 53520270
```

### Check Re-Analysis Status
```python
from src.services.rekordbox import RekordboxAdapter

adapter = RekordboxAdapter()
adapter.connect()

track = adapter.get_track_by_id(53520270)
# Check if Analysed == 0 (not analyzed)
```

## Summary

**Automatic re-analysis is now the default** for the link-local command, ensuring that:
- Waveforms match your local audio files
- Beat grids are accurate
- BPM detection is correct
- No manual work is needed

Use `--skip-reanalyze` only when you have a specific reason to preserve existing analysis data.

**Quick Start:**
```bash
# Most common usage (with automatic re-analysis)
python -m src.cli link-local --csv tracks.csv --apply

# Skip re-analysis if needed
python -m src.cli link-local --csv tracks.csv --apply --skip-reanalyze
```
