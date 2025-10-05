"""TagSelection model for managing user tag selection."""
from dataclasses import dataclass, field
from typing import List, Set, Optional
from models.tag import MyTag


@dataclass
class TagSelection:
    """Manages the state of user tag selection during interaction.
    
    Tracks available tags, selected tags, and validates selection.
    """
    
    available_tags: List[MyTag] = field(default_factory=list)
    selected_tag_ids: Set[int] = field(default_factory=set)
    selection_required: bool = True
    
    def __post_init__(self) -> None:
        """Initialize tag lookup dictionary."""
        self._tag_lookup = {tag.id: tag for tag in self.available_tags}
    
    def add_tag(self, tag: MyTag) -> None:
        """Add a tag to available tags."""
        if tag.id not in self._tag_lookup:
            self.available_tags.append(tag)
            self._tag_lookup[tag.id] = tag
    
    def toggle_tag(self, tag_id: int) -> bool:
        """Toggle selection of a tag by ID.
        
        Args:
            tag_id: ID of the tag to toggle
            
        Returns:
            True if tag is now selected, False if deselected
            
        Raises:
            ValueError: If tag_id not in available tags
        """
        if tag_id not in self._tag_lookup:
            raise ValueError(f"Tag ID {tag_id} not in available tags")
        
        if tag_id in self.selected_tag_ids:
            self.selected_tag_ids.remove(tag_id)
            return False
        else:
            self.selected_tag_ids.add(tag_id)
            return True
    
    def select_tag(self, tag_id: int) -> None:
        """Select a tag by ID."""
        if tag_id not in self._tag_lookup:
            raise ValueError(f"Tag ID {tag_id} not in available tags")
        self.selected_tag_ids.add(tag_id)
    
    def deselect_tag(self, tag_id: int) -> None:
        """Deselect a tag by ID."""
        self.selected_tag_ids.discard(tag_id)
    
    def select_all(self) -> None:
        """Select all available tags."""
        self.selected_tag_ids = {tag.id for tag in self.available_tags}
    
    def clear_selection(self) -> None:
        """Clear all selected tags."""
        self.selected_tag_ids.clear()
    
    def is_selected(self, tag_id: int) -> bool:
        """Check if a tag is selected."""
        return tag_id in self.selected_tag_ids
    
    def get_selected_tags(self) -> List[MyTag]:
        """Get list of selected tag objects."""
        return [self._tag_lookup[tag_id] for tag_id in self.selected_tag_ids
                if tag_id in self._tag_lookup]
    
    def get_selected_names(self) -> List[str]:
        """Get list of selected tag names."""
        return [tag.name for tag in self.get_selected_tags()]
    
    def validate_selection(self) -> None:
        """Validate that selection meets requirements.
        
        Raises:
            ValueError: If selection is invalid
        """
        if self.selection_required and not self.selected_tag_ids:
            raise ValueError("At least one tag must be selected")
    
    @property
    def selection_count(self) -> int:
        """Get number of selected tags."""
        return len(self.selected_tag_ids)
    
    @property
    def available_count(self) -> int:
        """Get number of available tags."""
        return len(self.available_tags)
    
    @property
    def is_valid(self) -> bool:
        """Check if current selection is valid."""
        if self.selection_required:
            return len(self.selected_tag_ids) > 0
        return True
    
    def __str__(self) -> str:
        """String representation of the selection."""
        return f"TagSelection({self.selection_count}/{self.available_count} selected)"
    
    def __repr__(self) -> str:
        """Developer representation of the selection."""
        return (f"TagSelection(available={self.available_count}, "
                f"selected={self.selection_count}, required={self.selection_required})")