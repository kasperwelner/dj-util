# Bandcamp Wishlist Automator

Automatically add tracks from a CSV file to your Bandcamp wishlist.

## Setup

### 1. Install Dependencies

```bash
pip3 install selenium
```

Or use the requirements file:

```bash
pip3 install -r requirements_bandcamp.txt
```

### 2. Install ChromeDriver

The script uses Chrome/Chromium. You need ChromeDriver installed:

**Option A: Using Homebrew (recommended for Mac)**
```bash
brew install chromedriver
```

**Option B: Manual Installation**
1. Download from: https://chromedriver.chromium.org/
2. Place in your PATH or in the same directory as the script

**Verify installation:**
```bash
chromedriver --version
```

## Usage

### Run the script:

```bash
python3 bandcamp_wishlist_automator.py
```

Or:

```bash
./bandcamp_wishlist_automator.py
```

### What it does:

1. **Prompts for credentials** - Enter your Bandcamp username/email and password
2. **Logs into Bandcamp** - Automatically logs you in
3. **Processes each track** from `Hard Groove.csv`:
   - Searches for the track on Bandcamp
   - Navigates to the track page
   - Checks if you already own it or have it wishlisted
   - Clicks the wishlist button if needed
   - Saves progress to `bandcamp_wishlist_progress.csv`

### Features:

- ✅ **Resume support** - If interrupted, run again and it picks up where it left off
- ✅ **Progress tracking** - All results saved to CSV with timestamps
- ✅ **Smart skipping** - Skips tracks you already own or have wishlisted
- ✅ **Error handling** - Handles missing tracks, network issues, etc.
- ✅ **Rate limiting** - 2-second delay between tracks (configurable)

### Progress File

Results are saved to `bandcamp_wishlist_progress.csv` with columns:
- `id` - Track ID from input CSV
- `artist` - Artist name
- `title` - Track title
- `status` - Result status:
  - `added` - Successfully added to wishlist
  - `already_wishlisted` - Was already in your wishlist
  - `owned` - You already own this track
  - `not_found` - Track not found on Bandcamp
  - `error` - An error occurred
- `bandcamp_url` - URL to the track page (if found)
- `notes` - Additional details
- `timestamp` - When it was processed

### Interrupting

Press `Ctrl+C` to stop. Your progress is saved automatically. Just run the script again to resume.

## Configuration

Edit these variables in `bandcamp_wishlist_automator.py`:

```python
INPUT_CSV = "Hard Groove.csv"          # Your input file
PROGRESS_CSV = "bandcamp_wishlist_progress.csv"  # Progress log
DELAY_BETWEEN_TRACKS = 2               # Seconds between tracks
```

## Troubleshooting

### "chromedriver not found"
- Install ChromeDriver (see setup above)
- Make sure it's in your PATH

### "Login failed"
- Double-check your username/password
- Check if Bandcamp requires 2FA (you may need to handle this manually)

### Script is too slow
- Reduce `DELAY_BETWEEN_TRACKS` (but be careful of rate limiting)

### Want to see the browser
- Comment out the headless option in the code (line 37):
  ```python
  # options.add_argument('--headless')
  ```

## Estimated Time

- ~3-5 seconds per track
- 128 tracks = ~6-10 minutes total

Much faster than manual processing! 🚀
