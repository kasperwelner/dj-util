#!/usr/bin/env python3
"""Diagnostic script to check track IDs in Rekordbox database."""

from src.services.rekordbox import RekordboxAdapter

def main():
    adapter = RekordboxAdapter()
    
    print("Connecting to Rekordbox database...")
    if not adapter.connect():
        print(f"✗ Error: {adapter.error_message}")
        return
    
    print("✓ Connected\n")
    
    # Get some streaming tracks
    print("Fetching first 5 streaming tracks...\n")
    streaming_tracks = adapter.get_streaming_tracks()[:5]
    
    if not streaming_tracks:
        print("No streaming tracks found!")
        return
    
    print(f"Found {len(streaming_tracks)} streaming tracks\n")
    print("=" * 80)
    
    for track in streaming_tracks:
        print(f"Track ID: {track.id}")
        print(f"Artist: {track.artist}")
        print(f"Title: {track.title}")
        print(f"Is Streaming: {track.is_streaming}")
        print("-" * 80)
    
    # Now try to look up the first track
    if streaming_tracks:
        test_id = streaming_tracks[0].id
        print(f"\nTrying to look up track with ID {test_id}...")
        found_track = adapter.get_track_by_id(test_id)
        
        if found_track:
            print(f"✓ Found: {found_track.artist} - {found_track.title}")
        else:
            print(f"✗ Not found!")
            print(f"Error: {adapter.error_message}")
    
    # Check specific ID from your CSV
    print(f"\n\nChecking ID from your CSV: 53520270")
    found_track = adapter.get_track_by_id(53520270)
    
    if found_track:
        print(f"✓ Found: {found_track.artist} - {found_track.title}")
        print(f"Is streaming: {found_track.is_streaming}")
    else:
        print(f"✗ Not found in database!")
        if adapter.error_message:
            print(f"Error: {adapter.error_message}")
    
    # Let's also check the raw database to see what ID field pyrekordbox is using
    print("\n\nChecking raw database content objects...")
    if adapter.db:
        try:
            contents = list(adapter.db.get_content())[:3]
            for content in contents:
                print(f"\nContent object attributes:")
                print(f"  ID: {content.ID if hasattr(content, 'ID') else 'N/A'}")
                print(f"  Title: {content.Title if hasattr(content, 'Title') else 'N/A'}")
                # Check for other ID-like fields
                for attr in dir(content):
                    if 'id' in attr.lower() and not attr.startswith('_'):
                        print(f"  {attr}: {getattr(content, attr, 'N/A')}")
        except Exception as e:
            print(f"Error accessing raw content: {e}")
    
    adapter.close()

if __name__ == "__main__":
    main()
