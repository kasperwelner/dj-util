# File Path Matcher for Rekordbox CSV

This script matches tracks from a Rekordbox CSV export with local music files in your filesystem, creating a new CSV that includes file paths.

## Features

- **Fuzzy Matching**: Uses advanced similarity algorithms to match track metadata with filenames
- **Title Match Requirement**: Requires partial title similarity to prevent false positives
- **Recursive Scanning**: Scans directories and all subdirectories for music files
- **Multiple Formats**: Supports common music formats (MP3, WAV, FLAC, AAC, M4A, OGG, WMA, AIFF, ALAC)
- **Smart Cleaning**: Intelligently removes parentheses, brackets, and common filename artifacts for better matching
- **Matched-Only Output**: CSV contains only successfully matched tracks (cleaner output)
- **Adjustable Similarity**: Configurable similarity threshold (default 0.6)
- **Progress Tracking**: Shows progress during processing
- **Match Summary**: Detailed statistics on matching success rate

## Usage

### Basic Usage

```bash
python3 file_path_matcher.py --input "Hard Groove.csv" --scan-dir "/Users/username/Music" --output "matched_tracks.csv"
```

### With Custom Similarity Threshold

```bash
python3 file_path_matcher.py -i tracks.csv -s ~/Music -o results.csv --similarity 0.7
```

### With Detailed Report

```bash
python3 file_path_matcher.py -i tracks.csv -s ~/Music -o results.csv --report-path "detailed_report.md"
```

### Command Line Options

- `--input, -i`: Path to input CSV file with rekordbox tracks (required)
- `--scan-dir, -s`: Directory to scan for music files recursively (required)  
- `--output, -o`: Path for output CSV file (required)
- `--similarity, -sim`: Similarity threshold for matching (0.0-1.0, default: 0.6)
- `--report-path, -r`: Path for detailed human-readable report (optional)

## Input CSV Format

The script expects a CSV file with these columns:
- `id` - Rekordbox track ID
- `artist` - Track artist name
- `title` - Track title
- `streaming` - Streaming status (Yes/No)

Example:
```csv
id,artist,title,streaming
130248411,Leod,Untitled 05,Yes
181447005,KVLR,6am,Yes
```

## Output CSV Format

The script generates a CSV with these columns:
- `rekordboxId` - Original Rekordbox track ID
- `artist` - Track artist name
- `song title` - Track title
- `file path` - Full path to matched music file

**Important**: The output CSV only contains successfully matched tracks. Unmatched tracks are excluded from the CSV output but are listed in the console summary and detailed report (if generated).

Example:
```csv
rekordboxId,artist,song title,file path
130248411,Leod,Untitled 05,/Users/music/Electronic/Leod - Untitled 05.mp3
181447005,KVLR,6am,/Users/music/House/KVLR - 6am.wav
```

## Detailed Report

When using `--report-path`, the script generates a comprehensive Markdown report containing:

### Report Sections

1. **Configuration**: Input parameters, scan directory, threshold settings
2. **Summary**: Total tracks, match statistics, success rate
3. **Confidence Distribution**: Breakdown of match quality (High ≥0.8, Medium 0.6-0.8, Low <0.6)
4. **Matched Tracks**: Complete list sorted by confidence score with visual confidence bars
5. **Unmatched Tracks**: Full list of tracks that couldn't be matched
6. **Recommendations**: Actionable suggestions for improving match rates

### Sample Report Output

```markdown
# File Path Matcher Report
Generated: 2025-10-01 22:30:09

## Summary
- **Total Tracks**: 100
- **Successfully Matched**: 85
- **Unmatched**: 15
- **Match Rate**: 85.0%

## Matched Tracks (Sorted by Confidence)

### 1. Leod - Untitled 05
- **Confidence**: 0.979 `█████████░`
- **File Path**: `~/Music/Electronic/Leod - Untitled 05.mp3`
```

## Matching Algorithm

The script uses multiple strategies to match tracks with enhanced accuracy:

1. **Text Cleaning**: Removes parentheses, brackets, special characters, and normalizes spaces
2. **Title Match Requirement**: **NEW** - Requires at least 30% similarity on the song title to prevent false positives
3. **Pattern Matching**: Tries different combinations:
   - "Artist Title"
   - "Title Artist"  
   - Title only
   - Artist only (only if title requirement is met)
4. **Similarity Scoring**: Uses sequence matching plus word-based matching for better results
5. **Best Match Selection**: Selects the file with highest similarity above the threshold

### Title Match Requirement

To reduce false positives, the algorithm now requires that the song title has at least partial similarity (30% threshold) with the filename. This means:

- ✅ **"Untitled 05"** will match **"Artist - Untitled 05.mp3"**
- ✅ **"6am"** will match **"KVLR - 6am.wav"**  
- ❌ **"Wrong Track"** will NOT match **"Artist - Completely Different Song.mp3"**
- ❌ **"House Music"** will NOT match **"Artist - Techno Beat.mp3"**

This prevents matches based solely on artist name when the song titles are completely different.

## Performance

The script processes tracks efficiently:
- Shows progress every 50 tracks
- Typical processing time: ~1-2 seconds per 100 tracks
- Memory usage: Loads all file paths into memory for fast matching

## Tips for Better Matching

1. **Lower similarity threshold** (0.4-0.5) for more matches, but may include false positives
2. **Higher similarity threshold** (0.7-0.8) for higher accuracy, but may miss some valid matches
3. **Clean filenames** work better - avoid excessive metadata in filenames
4. **Organize files** in artist/album folders for easier verification

## Troubleshooting

### No matches found
- Check that the scan directory contains music files
- Verify filename formats match artist/title patterns
- Try lowering the similarity threshold
- Check for encoding issues in CSV file

### Too many false matches
- Increase the similarity threshold
- Clean up filenames to remove excessive metadata
- Check for duplicate files in scan directory

### Performance issues
- Limit scan directory size (don't scan entire system)
- Use specific subdirectories if possible
- Consider splitting large CSV files

## Examples

### Match Hard Groove tracks with local music
```bash
python3 file_path_matcher.py --input "Hard Groove.csv" --scan-dir "~/Music/Electronic" --output "hard_groove_matched.csv"
```

### Match all streaming tracks with lower threshold
```bash
python3 file_path_matcher.py -i "all_streaming.csv" -s "/Volumes/Music" -o "streaming_matched.csv" --similarity 0.4
```

### Test with small dataset
```bash
python3 file_path_matcher.py -i "test_tracks.csv" -s "test_music" -o "test_results.csv"
```

### Generate detailed report
```bash
python3 file_path_matcher.py -i "Hard Groove.csv" -s "~/Music" -o "results.csv" --report-path "match_report.md"
```

## Integration with Existing Workflow

This script complements the existing Rekordbox export tools:

1. **Export tracks** using the main CLI: `rekordbox --tags "House"`
2. **Match with files** using this script: `python3 file_path_matcher.py -i house_tracks.csv -s ~/Music -o house_with_paths.csv`
3. **Process for Bandcamp** or other services using the enhanced CSV

The output CSV contains only matched tracks and maintains compatibility with existing processing scripts while adding valuable file path information. Use the detailed report (`--report-path`) to see which tracks couldn't be matched.
