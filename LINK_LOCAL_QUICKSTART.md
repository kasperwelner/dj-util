# Link Local Files - Quick Start Guide

## What It Does

The `link-local` command converts streaming tracks in Rekordbox (from Tidal, Beatport, Spotify, etc.) to reference local files on your disk by updating the Rekordbox database.

## Prerequisites

1. **Close Rekordbox** - The database must not be locked
2. **Virtual environment activated**: `source venv/bin/activate`
3. **CSV file** with track mappings (from file_path_matcher.py)
4. **ffmpeg installed** (optional, only for audio conversion): `brew install ffmpeg`

## Basic Workflow

### Step 1: Export Streaming Tracks
```bash
# Export tracks with specific tags
python -m src.cli export-command --tags "To Purchase"
```

### Step 2: Match with Local Files
```bash
# Find local files that match your streaming tracks
python3 file_path_matcher.py \
  --input "streaming_tracks.csv" \
  --scan-dir "~/Music" \
  --output "matched_tracks.csv"
```

### Step 3: Preview Changes (DRY-RUN)
```bash
# ALWAYS preview first!
python -m src.cli link-local --csv matched_tracks.csv
```

Review the output carefully. It will show:
- ✓ Tracks that will be updated
- ⊘ Tracks that will be skipped (already local, not found, etc.)
- ✗ Errors

### Step 4: Apply Changes
```bash
# If preview looks good, apply the changes
python -m src.cli link-local --csv matched_tracks.csv --apply
```

**⚠️ IMPORTANT**: Close Rekordbox before running with `--apply`!

## Common Usage Patterns

### Test with a Small Batch First
```bash
# Process only the first 3 tracks
python -m src.cli link-local --csv matched_tracks.csv --apply --limit 3
```

### Fuzzy Matching (No IDs Required)
If your CSV doesn't have Rekordbox IDs:
```bash
# Dry-run first
python -m src.cli link-local --csv tracks.csv --no-id-match

# Apply if matches look good
python -m src.cli link-local --csv tracks.csv --no-id-match --apply
```

### Adjust Fuzzy Matching Threshold
```bash
# Default is 0.75. Lower = more matches (but more false positives)
python -m src.cli link-local --csv tracks.csv --no-id-match \
  --match-threshold 0.65 --apply
```

### Audio Conversion
```bash
# Convert files to FLAC (lossless) while linking
python -m src.cli link-local --csv tracks.csv --convert-to flac --apply

# Convert to WAV with custom output directory
python -m src.cli link-local --csv tracks.csv \
  --convert-to wav \
  --conversion-dir ~/Music/Converted \
  --apply

# Convert to MP3 (320kbps)
python -m src.cli link-local --csv tracks.csv --convert-to mp3 --apply

# Convert to AIFF (Apple/Mac format)
python -m src.cli link-local --csv tracks.csv --convert-to aiff --apply

# Convert only MP3 and AAC files to FLAC
python -m src.cli link-local --csv tracks.csv \
  --convert-to flac \
  --convert-from mp3 --convert-from aac \
  --apply

# Preview conversion without executing
python -m src.cli link-local --csv tracks.csv --convert-to flac
```

## CSV Format

### With IDs (Recommended)
```csv
rekordboxId,artist,song title,file path
130248411,Leod,Untitled 05,/Users/you/Music/Leod - Untitled 05.flac
181447005,KVLR,6am,/Users/you/Music/KVLR - 6am.wav
```

### Without IDs (Fuzzy Matching)
```csv
artist,song title,file path
Leod,Untitled 05,/Users/you/Music/Leod - Untitled 05.flac
KVLR,6am,/Users/you/Music/KVLR - 6am.wav
```

## Safety Features

1. **Dry-run by default** - Must explicitly use `--apply` to make changes
2. **Automatic database backup** - Created before any writes
3. **File validation** - Checks that files exist before updating
4. **Streaming verification** - Only updates tracks that are actually streaming
5. **Automatic re-analysis** - Linked tracks are marked for re-analysis in Rekordbox (use `--skip-reanalyze` to disable)

## Troubleshooting

### "Database is locked"
- Close Rekordbox completely
- Check for background processes: `ps aux | grep Rekordbox`

### "ffmpeg not found"
- Install ffmpeg: `brew install ffmpeg` (macOS)
- Or download from: https://ffmpeg.org/download.html
- Verify installation: `ffmpeg -version`

### "Track ID not found"
- The ID in your CSV doesn't exist in Rekordbox
- Try fuzzy matching with `--no-id-match`

### "No match found" (Fuzzy Matching)
- Lower the threshold: `--match-threshold 0.6`
- Check that artist/title in CSV match database
- Verify tracks are actually streaming tracks

### "Artist/title mismatch"
- CSV metadata doesn't match database
- Use `--allow-mismatch` to proceed anyway
- Or fix the CSV to match database exactly

## After Running

1. **Open Rekordbox** - Linked tracks will be automatically re-analyzed
2. **Wait for analysis** - Rekordbox will regenerate waveforms and beat grids
3. **Verify tracks** - Check that they play correctly and analysis is accurate

Note: Re-analysis is automatic by default. Use `--skip-reanalyze` if you want to keep existing analysis data.

## Complete Example

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Export streaming tracks
python -m src.cli export-command --tags "Purchased"

# 3. Match with local files
python3 file_path_matcher.py \
  --input "purchased_streaming.csv" \
  --scan-dir "~/Music/Purchased" \
  --output "matched_purchased.csv"

# 4. Preview changes
python -m src.cli link-local --csv matched_purchased.csv

# 5. Test with 5 tracks first
python -m src.cli link-local --csv matched_purchased.csv --apply --limit 5

# 6. If successful, do the rest
python -m src.cli link-local --csv matched_purchased.csv --apply

# 7. Open Rekordbox and verify
```

## Advanced Options

```bash
# All options
python -m src.cli link-local \
  --csv matched_tracks.csv \
  --apply \
  --no-id-match \
  --match-threshold 0.75 \
  --limit 10 \
  --allow-mismatch \
  --force \
  --strict \
  --db-path "/custom/path/master.db" \
  --convert-to flac \
  --conversion-dir ~/Music/Converted
```

### Option Descriptions

- `--apply`: Actually execute changes (otherwise dry-run)
- `--no-id-match`: Use fuzzy artist/title matching
- `--match-threshold N`: Similarity threshold (0.0-1.0, default 0.75)
- `--limit N`: Process only first N rows
- `--allow-mismatch`: Proceed even if artist/title don't match exactly
- `--force`: Update tracks even if already local
- `--strict`: Stop on first error (default continues)
- `--db-path`: Explicit database path (auto-detects by default)
- `--convert-to FORMAT`: Convert audio files (wav, aiff, flac, mp3, aac, alac)
- `--convert-from FORMAT`: Only convert from specific source formats (can specify multiple)
- `--conversion-dir PATH`: Output directory for converted files
- `--skip-reanalyze`: Skip automatic re-analysis (keeps existing waveforms/beat grids)

## Database Backup Location

Backups are saved as: `master.backup.YYYYMMDD_HHMMSS.db`

In the same directory as your Rekordbox database (usually `~/Library/Pioneer/rekordbox/`)

To restore a backup:
1. Close Rekordbox
2. Rename backup to `master.db`
3. Restart Rekordbox

## Need Help?

Check the full specification: `LINK_LOCAL_FILES_SPEC.md`
