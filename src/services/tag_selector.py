"""TagSelector service for interactive tag selection."""
import sys
from typing import List, Optional, Set
from models.tag import MyTag
from models.tag_selection import TagSelection


class TagSelector:
    """Interactive tag selection service using terminal UI.
    
    Provides a checkbox-style interface for users to select
    multiple tags from a list.
    """
    
    def __init__(self):
        """Initialize the tag selector."""
        self.selection = TagSelection()
    
    def _build_hierarchy(self, tags: List[MyTag]) -> List[tuple]:
        """Build a hierarchy of tags grouped by parent.
        
        Args:
            tags: List of all tags
            
        Returns:
            List of (parent_name, children) tuples
        """
        # First, identify parent tags and build a map
        parent_tags = {}
        child_tags = {}
        orphan_tags = []
        
        for tag in tags:
            # Check if this tag has children (it's a parent)
            has_children = any(t for t in tags if hasattr(t, 'parent_id') and t.parent_id == tag.id)
            
            # For now, use a simple heuristic: tags with low IDs (1, 2, 3) are likely parents
            # Or tags without many tracks themselves
            if tag.id in ['1', '2', '3', '4', '5']:
                parent_tags[tag.id] = tag
                child_tags[tag.id] = []
        
        # Group tags by common patterns
        # Since we don't have explicit parent relationships in the model,
        # we'll use naming patterns and IDs
        genre_tags = []
        component_tags = []
        situation_tags = []
        other_tags = []
        
        # Known parent names from the hierarchy check
        genre_names = ['Hard Groove', 'Melodic Techno', 'Techno', 'House', 'Bass Music',
                      'Electro', 'Dubstep', 'Jungle', 'Tech House', 'Soulful House',
                      'UK Garage/2 Step', 'Minimal', 'African', 'Hypnotic', 'Electronic',
                      'Bassline House', 'Moombaton', 'Dub Techno', 'Melodic Bass',
                      'Drum & Bass', 'House (Commercial)', 'Hypnotic Techno', 'Amapiano',
                      'Disco/Funk']
        
        component_names = ['Synth', 'Vocal', 'Beat', 'Sub Bass', 'Percussion', 'Piano',
                          'Dark', 'Upper', 'Tactile', 'Layers']
        
        situation_names = ['Main Floor', 'Second Floor', 'Lounge', 'Mid Night', 'Morning',
                          'Early Night', 'Early Morning', 'Peak']
        
        for tag in tags:
            if tag.name in genre_names:
                genre_tags.append(tag)
            elif tag.name in component_names:
                component_tags.append(tag)
            elif tag.name in situation_names:
                situation_tags.append(tag)
            elif tag.name not in ['Genre', 'Components', 'Situation']:
                other_tags.append(tag)
        
        # Build the hierarchy list
        hierarchy = []
        
        if genre_tags:
            hierarchy.append(('🎵 GENRE', genre_tags))
        
        if component_tags:
            hierarchy.append(('🎛️ COMPONENTS', component_tags))
        
        if situation_tags:
            hierarchy.append(('🎭 SITUATION', situation_tags))
        
        if other_tags:
            hierarchy.append(('📌 OTHER', other_tags))
        
        return hierarchy
    
    def select_tags(self, tags: List[MyTag], preselected: Optional[Set[str]] = None) -> List[MyTag]:
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
        
        # Build hierarchy for display
        tag_hierarchy = self._build_hierarchy(tags)
        
        # For non-interactive environments or testing, return preselected
        if not sys.stdin.isatty():
            return [tag for tag in tags if tag.id in self.selection.selected_ids]
        
        try:
            import click
            
            # Display available tags grouped by category
            click.echo("\n" + "="*60)
            click.echo("AVAILABLE TAGS (grouped by category):")
            click.echo("="*60)
            
            # Create a flat list with numbers for selection
            tag_list = []
            tag_num = 1
            
            for parent_name, children in tag_hierarchy:
                if children:
                    click.echo(f"\n{parent_name}:")
                    click.echo("-" * len(parent_name))
                    
                    for tag in children:
                        marker = "[✓]" if tag.id in self.selection.selected_ids else "[ ]" 
                        count_str = f" ({tag.track_count} tracks)" if tag.track_count else ""
                        click.echo(f"{marker} {tag_num:3}. {tag.name}{count_str}")
                        tag_list.append(tag)
                        tag_num += 1
            
            click.echo("\n" + "="*60)
            click.echo("Enter tag numbers separated by commas (e.g., 1,3,5)")
            click.echo("Or enter tag names (e.g., House, Techno)")
            click.echo("Enter 'all' to select all tags, or press Enter to skip")
            click.echo("="*60)
            
            selection = click.prompt(
                "\nYour selection",
                default="",
                type=str,
                show_default=False
            )
            
            if not selection.strip():
                return []
            
            if selection.lower() == 'all':
                return tag_list
            
            selected_tags = []
            
            # Try to parse as numbers first
            try:
                indices = [int(x.strip()) - 1 for x in selection.split(',')]
                for i in indices:
                    if 0 <= i < len(tag_list):
                        selected_tags.append(tag_list[i])
            except ValueError:
                # Parse as tag names
                selected_names = set(name.strip() for name in selection.split(','))
                selected_tags = [tag for tag in tag_list if tag.name in selected_names]
            
            return selected_tags
            
        except ImportError:
            # Fallback to simple input if click not available
            print("\n" + "="*60)
            print("AVAILABLE TAGS (grouped by category):")
            print("="*60)
            
            # Create a flat list with numbers for selection
            tag_list = []
            tag_num = 1
            
            for parent_name, children in tag_hierarchy:
                if children:
                    print(f"\n{parent_name}:")
                    print("-" * len(parent_name))
                    
                    for tag in children:
                        marker = "[✓]" if tag.id in self.selection.selected_ids else "[ ]"
                        count_str = f" ({tag.track_count} tracks)" if tag.track_count else ""
                        print(f"{marker} {tag_num:3}. {tag.name}{count_str}")
                        tag_list.append(tag)
                        tag_num += 1
            
            print("\n" + "="*60)
            print("Enter tag numbers separated by commas (e.g., 1,3,5)")
            print("Or enter tag names (e.g., House, Techno)")
            print("Enter 'all' to select all tags, or press Enter to skip")
            print("="*60)
            
            selection = input("\nYour selection: ").strip()
            
            if selection.lower() == 'all':
                return tag_list
            
            if not selection:
                return []
            
            selected_tags = []
            
            # Try to parse as numbers first
            try:
                indices = [int(x.strip()) - 1 for x in selection.split(',')]
                for i in indices:
                    if 0 <= i < len(tag_list):
                        selected_tags.append(tag_list[i])
            except ValueError:
                # Parse as tag names
                selected_names = set(name.strip() for name in selection.split(','))
                selected_tags = [tag for tag in tag_list if tag.name in selected_names]
            
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