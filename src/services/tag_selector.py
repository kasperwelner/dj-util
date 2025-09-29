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
            
            # Display instructions
            click.echo("\nSelect tags using SPACE, navigate with UP/DOWN, confirm with ENTER")
            click.echo("Press 'a' to select all, 'n' to select none, 'q' to quit\n")
            
            # Simple implementation using click's choice
            # In a real implementation, we'd use a proper TUI library like curses or prompt_toolkit
            selected_names = click.prompt(
                "Select tags (comma-separated)",
                default="",
                type=str,
                show_default=False
            )
            
            if not selected_names.strip():
                return []
            
            # Parse selection
            selected_set = set(name.strip() for name in selected_names.split(','))
            return [tag for tag in tags if tag.name in selected_set]
            
        except ImportError:
            # Fallback to simple input if click not available
            print("\nAvailable tags:")
            for i, tag in enumerate(tags, 1):
                selected = "(selected)" if tag.id in self.selection.selected_ids else ""
                print(f"  {i}. {tag.name} {selected}")
            
            print("\nEnter tag numbers separated by commas (e.g., 1,3,5) or 'all' for all tags:")
            selection = input("> ").strip()
            
            if selection.lower() == 'all':
                return tags
            
            if not selection:
                return []
            
            try:
                indices = [int(x.strip()) - 1 for x in selection.split(',')]
                return [tags[i] for i in indices if 0 <= i < len(tags)]
            except (ValueError, IndexError):
                print("Invalid selection")
                return []
    
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