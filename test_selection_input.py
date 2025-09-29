#!/usr/bin/env python
"""Test tag selection with simulated input."""
import sys
from io import StringIO
from src.services.rekordbox import RekordboxAdapter
from src.services.tag_selector import TagSelector

def test_selection():
    adapter = RekordboxAdapter()
    if not adapter.connect():
        print(f"Failed to connect: {adapter.error_message}")
        return
    
    tags = adapter.get_all_mytags()
    print(f"\nFound {len(tags)} tags\n")
    
    selector = TagSelector()
    
    # Test 1: Select by numbers
    print("TEST 1: Selecting tags 2,3,4 by number")
    print("-" * 40)
    # Temporarily replace stdin to simulate user input
    old_stdin = sys.stdin
    sys.stdin = StringIO("2,3,4\n")
    
    selected = selector.select_tags(tags[:10])  # Use first 10 for display
    
    sys.stdin = old_stdin
    
    if selected:
        print(f"\nSelected {len(selected)} tags:")
        for tag in selected:
            print(f"  - {tag.name}")
    
    print("\n" + "="*60 + "\n")
    
    # Test 2: Select by names
    print("TEST 2: Selecting 'House' and 'Techno' by name")
    print("-" * 40)
    
    sys.stdin = StringIO("House, Techno\n")
    selected = selector.select_tags(tags)
    sys.stdin = old_stdin
    
    if selected:
        print(f"\nSelected {len(selected)} tags:")
        for tag in selected:
            print(f"  - {tag.name}")
    
    adapter.close()

if __name__ == "__main__":
    test_selection()