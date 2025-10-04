# New Audio Conversion Features

## ✨ What's New

### 1. AIFF Format Support ✅
Added **AIFF (Audio Interchange File Format)** as a conversion target and source format.

**Format Details:**
- Codec: PCM 16-bit signed big-endian
- Container: `.aiff`
- Quality: Lossless, uncompressed
- File Size: Same as WAV (~100% of original PCM)
- Best For: Mac/Apple compatibility, Logic Pro, professional audio on macOS

**Why AIFF?**
- Native Apple/Mac audio format
- Standard in Logic Pro and GarageBand
- Slightly different byte order than WAV (big-endian vs little-endian)
- Fully compatible with macOS audio tools

**Usage:**
```bash
# Convert tracks to AIFF
python -m src.cli link-local --csv tracks.csv --convert-to aiff --apply

# Convert AIFF files to FLAC
python -m src.cli link-local --csv tracks.csv --convert-to flac --convert-from aiff --apply
```

---

### 2. Source Format Filtering (`--convert-from`) ✅
Added the ability to **selectively convert only specific source formats**.

**Why This Matters:**
- Convert only lossy formats (MP3, AAC) to lossless (FLAC)
- Skip files that are already in acceptable formats
- Reduce unnecessary processing and disk usage
- More control over batch conversions

**How It Works:**
```bash
# Only convert MP3 and AAC files to FLAC
# (WAV, FLAC, AIFF files will be linked as-is)
python -m src.cli link-local --csv tracks.csv \
  --convert-to flac \
  --convert-from mp3 \
  --convert-from aac \
  --apply
```

**Multiple Filters:**
You can specify multiple `--convert-from` flags to include multiple source formats:
```bash
--convert-from mp3 --convert-from aac --convert-from wav
```

**Behavior:**
- If `--convert-from` is specified, only files matching those formats will be converted
- Other files will be linked to Rekordbox without conversion
- The system automatically normalizes format extensions (e.g., `.aif` → `aiff`, `.m4a` → `aac`)

---

## 📋 Updated Format List

| Format | Codec | Container | Type | Quality | Size | Use Case |
|--------|-------|-----------|------|---------|------|----------|
| **WAV** | PCM 16-bit LE | .wav | Lossless | Perfect | 100% | PC/Windows, Universal |
| **AIFF** | PCM 16-bit BE | .aiff | Lossless | Perfect | 100% | **Mac/Apple, Logic Pro** ⭐ NEW |
| **FLAC** | FLAC | .flac | Lossless | Perfect | ~50-60% | Best compression ratio |
| **MP3** | libmp3lame | .mp3 | Lossy | 320kbps | ~15-20% | Universal compatibility |
| **AAC** | AAC | .m4a | Lossy | 256kbps | ~15-20% | Apple ecosystem |
| **ALAC** | ALAC | .m4a | Lossless | Perfect | ~50-60% | Apple lossless |

---

## 🎯 Common Use Cases

### Use Case 1: Convert Lossy to Lossless
**Scenario:** You have a mix of MP3/AAC files and already-lossless files. You want to convert only the lossy ones to FLAC.

```bash
python -m src.cli link-local --csv mixed_library.csv \
  --convert-to flac \
  --convert-from mp3 \
  --convert-from aac \
  --apply
```

**Result:**
- MP3 files → Converted to FLAC
- AAC files → Converted to FLAC
- WAV/FLAC/AIFF files → Linked as-is (no conversion)

---

### Use Case 2: Mac User Converting Everything to AIFF
**Scenario:** Logic Pro user wants all tracks in AIFF format for maximum compatibility.

```bash
python -m src.cli link-local --csv tracks.csv \
  --convert-to aiff \
  --apply
```

**Result:**
- All non-AIFF files → Converted to AIFF
- AIFF files → Linked as-is

---

### Use Case 3: Selective Uncompressed to Compressed
**Scenario:** Convert only large uncompressed files (WAV/AIFF) to FLAC to save space.

```bash
python -m src.cli link-local --csv tracks.csv \
  --convert-to flac \
  --convert-from wav \
  --convert-from aiff \
  --conversion-dir ~/Music/FLAC \
  --apply
```

**Result:**
- WAV files → Converted to FLAC (saves ~50% disk space)
- AIFF files → Converted to FLAC (saves ~50% disk space)
- MP3/AAC/ALAC → Linked as-is

---

## 🔧 Technical Implementation

### Audio Converter Enhancement
- Added AIFF codec configuration (PCM 16-bit big-endian)
- Format normalization: `.aif` and `.aiff` are treated as the same format

### LinkLocalService Enhancement
- New `convert_from_formats` parameter
- Format filtering logic before conversion
- Source format detection with normalization
- Clear user feedback when skipping conversions

### CLI Enhancement
- New `--convert-from` option (can be specified multiple times)
- Updated `--convert-to` choices to include `aiff`
- Validation: `--convert-from` requires `--convert-to`
- Header display shows active filters

---

## 📖 Updated Documentation

All documentation has been updated:

1. **AUDIO_CONVERSION.md**
   - Added AIFF format details
   - Added `--convert-from` examples
   - Updated format comparison tables

2. **LINK_LOCAL_QUICKSTART.md**
   - Added AIFF conversion examples
   - Added filtering examples
   - Updated option descriptions

3. **WARP.md**
   - Added new command examples
   - Updated notes about supported formats

---

## ✅ Testing

All features have been tested:

```bash
# Test AIFF as target
✓ python -m src.cli link-local --csv tracks.csv --convert-to aiff

# Test filtering (only WAV)
✓ python -m src.cli link-local --csv tracks.csv --convert-to flac --convert-from wav

# Test multiple filters
✓ python -m src.cli link-local --csv tracks.csv --convert-to flac --convert-from aiff --convert-from wav

# Test header display
✓ Shows "Convert only from: AIFF, WAV" when filters active

# Test skip message
✓ Shows "Skipping conversion (source format AIFF not in filter)" when filtered out
```

---

## 🎉 Summary

Two powerful new features enhance the audio conversion capabilities:

1. **AIFF Support**: Full format support for Apple/Mac users and Logic Pro workflows
2. **Selective Conversion**: Fine-grained control over which files get converted based on source format

Both features work seamlessly with all existing functionality (dry-run, fuzzy matching, database backup, etc.).

**Complete Command Example:**
```bash
python -m src.cli link-local \
  --csv tracks.csv \
  --convert-to flac \
  --convert-from mp3 --convert-from aac --convert-from wav \
  --conversion-dir ~/Music/Lossless \
  --limit 10 \
  --apply
```

This command will:
- Process first 10 tracks
- Convert only MP3, AAC, and WAV files to FLAC
- Save converted files to ~/Music/Lossless
- Link all tracks (converted or original) to Rekordbox
- Skip FLAC, AIFF, and ALAC files (no conversion needed)
