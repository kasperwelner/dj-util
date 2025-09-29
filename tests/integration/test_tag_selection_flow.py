"""Integration tests for interactive tag selection flow."""
import pytest
from unittest.mock import Mock, patch
from src.services.tag_selector import TagSelector
from src.models.tag import MyTag


class TestTagSelectionFlow:
    """Test the complete tag selection workflow."""
    
    def test_display_all_available_tags(self):
        """Test that all MyTags from database are displayed for selection."""
        selector = TagSelector()
        tags = [
            MyTag(id=1, name="Deep House"),
            MyTag(id=2, name="Techno"),
            MyTag(id=3, name="House")
        ]
        
        with patch('click.Choice') as mock_choice:
            displayed_tags = selector.display_tags(tags)
            assert len(displayed_tags) == 3
            assert "Deep House" in displayed_tags
    
    def test_user_can_select_multiple_tags(self):
        """Test user can select and deselect multiple tags."""
        selector = TagSelector()
        tags = [MyTag(id=1, name="Tag1"), MyTag(id=2, name="Tag2")]
        
        with patch('click.prompt') as mock_prompt:
            mock_prompt.return_value = ["Tag1", "Tag2"]
            selected = selector.get_user_selection(tags)
            assert len(selected) == 2
    
    def test_requires_at_least_one_tag_selection(self):
        """Test validation that at least one tag must be selected."""
        selector = TagSelector()
        
        with pytest.raises(ValueError, match="At least one tag must be selected"):
            selector.validate_selection([])
    
    def test_handles_unicode_tag_names(self):
        """Test that Unicode tag names are displayed correctly."""
        selector = TagSelector()
        tags = [
            MyTag(id=1, name="日本語"),
            MyTag(id=2, name="Русский"),
            MyTag(id=3, name="🎵 Music")
        ]
        
        displayed = selector.display_tags(tags)
        assert "日本語" in displayed
        assert "🎵 Music" in displayed