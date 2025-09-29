"""TagSelector service for interactive tag selection."""
import sys
from typing import List, Optional, Set
from src.models.tag import MyTag
from src.models.tag_selection import TagSelection


class TagSelector:
    """Interactive tag selection service using terminal UI.
    
    Provides a checkbox-style interface for users to select
    multiple tags from a list.
    """
    
    def __init__(self):
        """Initialize the tag selector."""
        self.selection = TagSelection()
    
    def select_tags(self, tags: List[MyTag], preselected: Optional[Set[int]] = None) -> List[MyTag]:
        """Display interactive tag selection interface.
        
        Args:
            tags: List of available tags to choose from
            preselected: Optional set of tag IDs to preselect
            
        Returns:
            List of selected MyTag objects
        """
        if not tags:
            return []
        
        # Initialize selection state
        self.selection.available_tags = tags
        self.selection.selected_ids = preselected or set()
        self.selection.current_index = 0
        
        # For non-interactive environments or testing, return preselected
        if not sys.stdin.isatty():
            return [tag for tag in tags if tag.id in self.selection.selected_ids]
        
        try:
            import click
            
            # Display available tags with numbers
            click.echo("\n" + "="*50)
            click.echo("AVAILABLE TAGS:")
            click.echo("="*50)
            
            # Use compact display if more than 20 tags
            if len(tags) > 20:
                click.echo("")
                # Show in columns
                for i in range(0, len(tags), 3):
                    row = []
                    for j in range(3):
                        if i + j < len(tags):
                            tag = tags[i + j]
                            num = i + j + 1
                            row.append(f"{num:2}. {tag.name[:20]:<20}")
                    click.echo("  " + "  ".join(row))
                click.echo("")
            else:
                for i, tag in enumerate(tags, 1):
                    # Show selection state if preselected
                    marker = "[✓]" if tag.id in self.selection.selected_ids else "[ ]" 
                    # Show track count if available
                    count_str = f" ({tag.track_count} tracks)" if tag.track_count else ""
                    click.echo(f"{marker} {i:3}. {tag.name}{count_str}")
            
            click.echo("\n" + "="*50)
            click.echo("Enter tag numbers separated by commas (e.g., 1,3,5)")
            click.echo("Or enter tag names (e.g., House, Techno)")
            click.echo("Enter 'all' to select all tags, or press Enter to skip")
            click.echo("="*50)
            
            selection = click.prompt(
                "\nYour selection",
                default="",
                type=str,
                show_default=False
            )
            
            if not selection.strip():
                return []
            
            if selection.lower() == 'all':
                return tags
            
            selected_tags = []
            
            # Try to parse as numbers first
            try:
                indices = [int(x.strip()) - 1 for x in selection.split(',')]
                for i in indices:
                    if 0 <= i < len(tags):
                        selected_tags.append(tags[i])
            except ValueError:
                # Parse as tag names
                selected_names = set(name.strip() for name in selection.split(','))
                selected_tags = [tag for tag in tags if tag.name in selected_names]
            
            return selected_tags
            
        except ImportError:
            # Fallback to simple input if click not available
            print("\n" + "="*50)
            print("AVAILABLE TAGS:")
            print("="*50)
            
            for i, tag in enumerate(tags, 1):
                marker = "[✓]" if tag.id in self.selection.selected_ids else "[ ]"
                count_str = f" ({tag.track_count} tracks)" if tag.track_count else ""
                print(f"{marker} {i:3}. {tag.name}{count_str}")
            
            print("\n" + "="*50)
            print("Enter tag numbers separated by commas (e.g., 1,3,5)")
            print("Or enter tag names (e.g., House, Techno)")
            print("Enter 'all' to select all tags, or press Enter to skip")
            print("="*50)
            
            selection = input("\nYour selection: ").strip()
            
            if selection.lower() == 'all':
                return tags
            
            if not selection:
                return []
            
            selected_tags = []
            
            # Try to parse as numbers first
            try:
                indices = [int(x.strip()) - 1 for x in selection.split(',')]
                for i in indices:
                    if 0 <= i < len(tags):
                        selected_tags.append(tags[i])
            except ValueError:
                # Parse as tag names
                selected_names = set(name.strip() for name in selection.split(','))
                selected_tags = [tag for tag in tags if tag.name in selected_names]
            
            if not selected_tags:
                print("No valid tags selected")
            
            return selected_tags
    
    def display_summary(self, selected_tags: List[MyTag]) -> None:
        """Display summary of selected tags.
        
        Args:
            selected_tags: List of selected tags to summarize
        """
        if not selected_tags:
            print("\nNo tags selected")
            return
        
        print(f"\nSelected {len(selected_tags)} tag(s):")
        for tag in selected_tags:
            track_info = f" ({tag.track_count} tracks)" if tag.track_count else ""
            print(f"  • {tag.name}{track_info}")
    
    def confirm_selection(self, selected_tags: List[MyTag]) -> bool:
        """Ask user to confirm their selection.
        
        Args:
            selected_tags: Tags to confirm
            
        Returns:
            True if user confirms, False otherwise
        """
        if not selected_tags:
            return False
        
        self.display_summary(selected_tags)
        
        try:
            import click
            return click.confirm("\nProceed with export?", default=True)
        except ImportError:
            # Fallback to simple input
            response = input("\nProceed with export? [Y/n]: ").strip().lower()
            return response in ('', 'y', 'yes')