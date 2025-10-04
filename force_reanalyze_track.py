#!/usr/bin/env python3
"""Script to force Rekordbox to re-analyze a track."""

import sys
from src.services.rekordbox import RekordboxAdapter


def main():
    if len(sys.argv) < 2:
        print("Usage: python force_reanalyze_track.py <track_id>")
        print("Example: python force_reanalyze_track.py 53520270")
        sys.exit(1)
    
    try:
        track_id = int(sys.argv[1])
    except ValueError:
        print(f"Error: '{sys.argv[1]}' is not a valid track ID (must be an integer)")
        sys.exit(1)
    
    print("=" * 60)
    print("Force Track Re-Analysis")
    print("=" * 60)
    print(f"Track ID: {track_id}")
    print()
    
    # Connect to database
    adapter = RekordboxAdapter()
    
    print("Connecting to Rekordbox database...")
    if not adapter.connect():
        print(f"✗ Error: {adapter.error_message}")
        sys.exit(1)
    
    print("✓ Connected")
    print()
    
    # Get track info first
    print("Fetching track information...")
    track = adapter.get_track_by_id(track_id)
    
    if not track:
        print(f"✗ Track ID {track_id} not found in database")
        if adapter.error_message:
            print(f"   Error: {adapter.error_message}")
        adapter.close()
        sys.exit(1)
    
    print(f"✓ Found: {track.artist} - {track.title}")
    print()
    
    # Backup database first
    print("Creating database backup...")
    backup_path = adapter.backup_database()
    
    if backup_path:
        print(f"✓ Backup created: {backup_path.name}")
    else:
        print(f"✗ Failed to backup: {adapter.error_message}")
        print("⚠ Proceeding anyway (not recommended)")
    print()
    
    # Force re-analysis
    print("Clearing analysis data to force re-analysis...")
    success = adapter.force_reanalyze(track_id)
    
    if success:
        print("✓ Analysis data cleared successfully!")
        print()
        print("Next steps:")
        print("1. Open Rekordbox")
        print("2. Navigate to the track")
        print("3. Rekordbox should automatically re-analyze it")
        print("   (or you can manually trigger analysis)")
        print()
        print("The track should now have a fresh beat grid and waveform.")
    else:
        print(f"✗ Failed to clear analysis data")
        print(f"   Error: {adapter.error_message}")
        sys.exit(1)
    
    adapter.close()
    print("=" * 60)


if __name__ == "__main__":
    main()
