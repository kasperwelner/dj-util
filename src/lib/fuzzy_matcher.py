"""Fuzzy matching utility for artist/title matching."""
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import List, Optional
from models.track import Track


@dataclass
class MatchCandidate:
    """Represents a potential match from database."""
    track_id: int
    artist: str
    title: str
    similarity: float
    ambiguous: bool = False


class FuzzyMatcher:
    """Match tracks using artist+title similarity."""
    
    def __init__(self, threshold: float = 0.75):
        """Initialize fuzzy matcher.
        
        Args:
            threshold: Minimum similarity score (0.0-1.0)
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0")
        self.threshold = threshold
    
    def clean_text(self, text: str) -> str:
        """Clean text for matching.
        
        Same approach as file_path_matcher.py:
        - Remove parentheses and brackets content
        - Remove special characters
        - Normalize whitespace
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned lowercase text
        """
        if not text:
            return ""
        
        # Remove content in parentheses and brackets
        text = re.sub(r'\([^)]*\)', '', text)
        text = re.sub(r'\[[^\]]*\]', '', text)
        
        # Remove special characters
        text = re.sub(r'[^\w\s]', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text.lower()
    
    def calculate_similarity(
        self,
        csv_artist: str,
        csv_title: str,
        db_artist: str,
        db_title: str
    ) -> float:
        """Calculate combined similarity score.
        
        Uses same approach as bandcamp_wishlist_automator.py:
        combines artist + title into single search query.
        
        Args:
            csv_artist: Artist from CSV
            csv_title: Title from CSV
            db_artist: Artist from database
            db_title: Title from database
            
        Returns:
            Similarity score (0.0-1.0)
        """
        # Combine artist + title for both
        csv_query = self.clean_text(f"{csv_artist} {csv_title}")
        db_query = self.clean_text(f"{db_artist} {db_title}")
        
        if not csv_query or not db_query:
            return 0.0
        
        # Sequence similarity (70% weight)
        sequence_sim = SequenceMatcher(None, csv_query, db_query).ratio()
        
        # Word overlap similarity (30% weight)
        csv_words = set(csv_query.split())
        db_words = set(db_query.split())
        
        if csv_words and db_words:
            intersection = len(csv_words.intersection(db_words))
            union = len(csv_words.union(db_words))
            word_sim = intersection / union if union > 0 else 0.0
        else:
            word_sim = 0.0
        
        # Combined score
        return (sequence_sim * 0.7) + (word_sim * 0.3)
    
    def find_best_match(
        self,
        csv_artist: str,
        csv_title: str,
        db_tracks: List[Track]
    ) -> Optional[MatchCandidate]:
        """Find best matching track from database.
        
        Args:
            csv_artist: Artist from CSV
            csv_title: Title from CSV
            db_tracks: List of tracks from database to search
            
        Returns:
            MatchCandidate if found above threshold, None otherwise
        """
        candidates = []
        
        for track in db_tracks:
            similarity = self.calculate_similarity(
                csv_artist, csv_title,
                track.artist or '', track.title or ''
            )
            
            if similarity >= self.threshold:
                candidates.append(MatchCandidate(
                    track_id=track.id,
                    artist=track.artist or '',
                    title=track.title or '',
                    similarity=similarity
                ))
        
        if not candidates:
            return None
        
        # Sort by similarity (descending)
        candidates.sort(key=lambda c: c.similarity, reverse=True)
        
        # Check for ambiguity (multiple close matches)
        best = candidates[0]
        if len(candidates) > 1:
            second_best = candidates[1]
            if best.similarity - second_best.similarity < 0.05:
                # Ambiguous match (within 0.05 similarity)
                best.ambiguous = True
        
        return best
