# Audio Conversion Feature

## Overview

The link-local command now supports automatic audio format conversion using ffmpeg. This allows you to convert streaming tracks to a different format as part of the linking process.

## Installation

### macOS
```bash
brew install ffmpeg
```

### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

### Windows
Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)

### Verify Installation
```bash
ffmpeg -version
```

## Supported Formats

| Format | Description | Quality | Use Case |
|--------|-------------|---------|----------|
| **WAV** | PCM 16-bit LE | Lossless, uncompressed | Maximum compatibility, large files |
| **AIFF** | PCM 16-bit BE | Lossless, uncompressed | Apple/Mac compatibility, large files |
| **FLAC** | Free Lossless Audio Codec | Lossless, compressed | Best quality-to-size ratio |
| **MP3** | MPEG Audio Layer III | 320 kbps | Universal compatibility, smaller files |
| **AAC** | Advanced Audio Coding | 256 kbps | Good quality, Apple ecosystem |
| **ALAC** | Apple Lossless Audio Codec | Lossless, compressed | Apple ecosystem, lossless |

## Usage

### Basic Conversion

```bash
# Convert to FLAC (recommended for lossless)
python -m src.cli link-local --csv tracks.csv --convert-to flac --apply

# Convert to WAV (maximum compatibility)
python -m src.cli link-local --csv tracks.csv --convert-to wav --apply

# Convert to MP3 (smallest files)
python -m src.cli link-local --csv tracks.csv --convert-to mp3 --apply

# Convert to AIFF (Apple/Mac format)
python -m src.cli link-local --csv tracks.csv --convert-to aiff --apply
```

### With Custom Output Directory

```bash
# Convert to FLAC in a specific directory
python -m src.cli link-local --csv tracks.csv \
  --convert-to flac \
  --conversion-dir ~/Music/Converted \
  --apply
```

### Preview Conversions (Dry-Run)

```bash
# See what would be converted without executing
python -m src.cli link-local --csv tracks.csv --convert-to flac
```

### Combined with Other Options

```bash
# Fuzzy matching + conversion + custom output
python -m src.cli link-local --csv tracks.csv \
  --no-id-match \
  --convert-to flac \
  --conversion-dir ~/Music/Lossless \
  --apply

# Test with first 3 tracks
python -m src.cli link-local --csv tracks.csv \
  --convert-to wav \
  --limit 3 \
  --apply

# Convert only MP3 and AAC files to FLAC (filtering by source format)
python -m src.cli link-local --csv tracks.csv \
  --convert-to flac \
  --convert-from mp3 \
  --convert-from aac \
  --apply
```

## Behavior

### Smart Conversion
- **Only converts when needed**: If source is already in target format, skips conversion
- **Preserves original**: Original files are kept by default
- **Updates database**: Rekordbox is updated to point to the converted file

### File Naming
Converted files use the same base name as the source:
- `track.mp3` → `track.flac`
- `song.wav` → `song.mp3`

### Output Location
- **Default**: Same directory as source file
- **Custom**: Specify with `--conversion-dir`

### Error Handling
- **Conversion fails**: Falls back to using original file
- **File already exists**: Skips conversion (won't overwrite)
- **ffmpeg not found**: Clear error with installation instructions

## Examples

### Example 1: Convert Streaming MP3s to Lossless FLAC
```bash
# 1. Export streaming tracks
python -m src.cli export-command --tags "To Convert"

# 2. Match with local MP3 files
python3 file_path_matcher.py \
  --input "streaming_tracks.csv" \
  --scan-dir "~/Music/MP3" \
  --output "matched_mp3s.csv"

# 3. Convert to FLAC while linking
python -m src.cli link-local --csv matched_mp3s.csv \
  --convert-to flac \
  --conversion-dir ~/Music/FLAC \
  --apply
```

### Example 2: Convert Various Formats to WAV for DJ Performance
```bash
# Convert everything to WAV for maximum compatibility
python -m src.cli link-local --csv mixed_formats.csv \
  --convert-to wav \
  --conversion-dir ~/Music/WAV \
  --apply
```

### Example 3: Convert Large Library in Batches
```bash
# Test with first 10 tracks
python -m src.cli link-local --csv library.csv \
  --convert-to flac \
  --limit 10 \
  --apply

# If successful, process the rest
python -m src.cli link-local --csv library.csv \
  --convert-to flac \
  --apply
```

## Technical Details

### Conversion Settings

#### WAV
- Codec: PCM 16-bit signed little-endian
- Container: `.wav`
- Lossless, uncompressed
- Best for: PC/Windows compatibility

#### AIFF
- Codec: PCM 16-bit signed big-endian
- Container: `.aiff`
- Lossless, uncompressed
- Best for: Mac/Apple compatibility, Logic Pro

#### FLAC
- Codec: FLAC
- Container: `.flac`
- Compression level: 8 (maximum)
- Lossless, compressed (~50-60% of WAV size)

#### MP3
- Codec: libmp3lame
- Container: `.mp3`
- Bitrate: 320 kbps (CBR)
- Lossy compression

#### AAC
- Codec: AAC
- Container: `.m4a`
- Bitrate: 256 kbps
- Lossy compression, better than MP3 at same bitrate

#### ALAC
- Codec: Apple Lossless (ALAC)
- Container: `.m4a`
- Lossless, compressed (similar to FLAC)

### Metadata Preservation
All conversions preserve the following metadata:
- Artist
- Title
- Album
- Genre
- Year
- Other ID3/Vorbis comments

### Performance
- Conversion is CPU-intensive (uses ffmpeg)
- Timeout: 5 minutes per file
- Typical conversion time: 5-30 seconds per track
- FLAC compression is slower but creates smaller files

## Troubleshooting

### ffmpeg not found
```
Error: ffmpeg not found. Install it with: brew install ffmpeg (macOS)
```
**Solution**: Install ffmpeg using the commands in the Installation section above.

### Conversion timeout
```
Error: Conversion timed out (>5 minutes)
```
**Solution**: This is rare, but may happen with very large files or slow systems. The original file will be used instead.

### Output file already exists
```
Error: Output file already exists: /path/to/track.flac
```
**Solution**: The converter won't overwrite existing files. Delete the existing file or use a different output directory.

### Conversion failed
```
⚠ Conversion failed: ffmpeg error: ...
→ Using original file instead
```
**Solution**: The system will fall back to the original file. Check that the source file is valid and not corrupted.

## Best Practices

### 1. Test First
Always run with `--limit` first to test on a small batch:
```bash
python -m src.cli link-local --csv tracks.csv --convert-to flac --limit 3 --apply
```

### 2. Use Dry-Run
Preview what will be converted:
```bash
python -m src.cli link-local --csv tracks.csv --convert-to flac
```

### 3. Choose the Right Format
- **Lossless needed?** → FLAC or ALAC
- **Maximum compatibility?** → WAV or MP3
- **Smaller files?** → MP3 or AAC
- **Apple ecosystem?** → ALAC or AAC

### 4. Organize Output
Use `--conversion-dir` to keep converted files organized:
```bash
--conversion-dir ~/Music/Lossless
--conversion-dir ~/Music/WAV
--conversion-dir ~/Music/Converted
```

### 5. Backup Database
The system automatically backs up your Rekordbox database before making changes, but it's always good to have your own backup.

## Format Comparison

| Format | Lossless | Compression | File Size (relative) | Quality | Compatibility |
|--------|----------|-------------|---------------------|---------|---------------|
| WAV    | ✓        | None        | 100%                | Perfect | Universal     |
| AIFF   | ✓        | None        | 100%                | Perfect | Mac/Apple     |
| FLAC   | ✓        | Yes         | ~50-60%             | Perfect | Very Good     |
| ALAC   | ✓        | Yes         | ~50-60%             | Perfect | Apple-focused |
| MP3    | ✗        | Yes         | ~15-20%             | Very Good | Universal   |
| AAC    | ✗        | Yes         | ~15-20%             | Very Good | Good        |

## Integration with Workflow

The audio conversion feature integrates seamlessly with the full workflow:

```bash
# 1. Export streaming tracks from Rekordbox
python -m src.cli export-command --tags "Purchased"

# 2. Match with local files
python3 file_path_matcher.py -i purchased.csv -s ~/Downloads -o matched.csv

# 3. Link + Convert in one step
python -m src.cli link-local --csv matched.csv \
  --convert-to flac \
  --conversion-dir ~/Music/FLAC \
  --apply

# 4. Open Rekordbox and verify
```

All tracks are now linked to local FLAC files in your Rekordbox library!
