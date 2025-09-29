#!/usr/bin/env python
"""Test interactive tag selection display."""
from src.services.rekordbox import RekordboxAdapter
from src.services.tag_selector import TagSelector

def main():
    adapter = RekordboxAdapter()
    if not adapter.connect():
        print(f"Failed to connect: {adapter.error_message}")
        return
    
    tags = adapter.get_all_mytags()
    print(f"Found {len(tags)} tags from database")
    
    # Limit to first 10 for testing
    test_tags = tags[:10]
    
    selector = TagSelector()
    # Simulate the interface without actual interaction
    print("\nThis is what the interface will show:")
    print("="*60)
    
    import click
    click.echo("\n" + "="*50)
    click.echo("AVAILABLE TAGS:")
    click.echo("="*50)
    
    for i, tag in enumerate(test_tags, 1):
        marker = "[ ]"  # No preselection
        count_str = f" ({tag.track_count} tracks)" if tag.track_count else ""
        click.echo(f"{marker} {i:3}. {tag.name}{count_str}")
    
    click.echo("\n" + "="*50)
    click.echo("Enter tag numbers separated by commas (e.g., 1,3,5)")
    click.echo("Or enter tag names (e.g., House, Techno)")
    click.echo("Enter 'all' to select all tags, or press Enter to skip")
    click.echo("="*50)
    print("\n[Then it would show: 'Your selection: ' prompt]")
    
    adapter.close()

if __name__ == "__main__":
    main()