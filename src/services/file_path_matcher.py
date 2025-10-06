"""File Path Matcher Service for Rekordbox CSV.

This service takes a CSV file with rekordbox track data (id, artist, title, streaming)
and scans a given folder structure to find matching music files, creating a new CSV
with file paths added.

The matching algorithm requires at least partial similarity on the song title (30% threshold)
to prevent false positives based solely on artist name matches.
"""

import csv
import os
import re
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import List, Optional

from models.music_file import MusicFile
from models.track_record import TrackRecord

# Common music file extensions
MUSIC_EXTENSIONS = {'.mp3', '.wav', '.flac', '.aac', '.m4a', '.ogg', '.wma', '.aiff', '.alac'}


class FilePathMatcher:
    """Main class for matching CSV tracks with music files."""

    def __init__(self, similarity_threshold: float = 0.6):
        """Initialize the matcher.

        Args:
            similarity_threshold: Minimum similarity score (0.0-1.0) for matching
        """
        self.similarity_threshold = similarity_threshold
        self.music_files: List[MusicFile] = []
        self.tracks: List[TrackRecord] = []
        self.duplicate_files_resolved = 0

    def load_csv_tracks(self, csv_path: str) -> List[TrackRecord]:
        """Load tracks from the input CSV file."""
        tracks = []

        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        with open(csv_path, 'r', encoding='utf-8-sig', newline='') as file:
            reader = csv.DictReader(file)

            # Validate required columns
            required_cols = {'id', 'artist', 'title', 'streaming'}
            if not required_cols.issubset(set(reader.fieldnames)):
                raise ValueError(f"CSV must contain columns: {required_cols}")

            for row in reader:
                track = TrackRecord(
                    rekordbox_id=row['id'],
                    artist=row['artist'] or '',
                    title=row['title'] or '',
                    streaming=row['streaming']
                )
                tracks.append(track)

        print(f"Loaded {len(tracks)} tracks from {csv_path}")
        return tracks

    def scan_music_files(self, scan_dir: str) -> List[MusicFile]:
        """Recursively scan directory for music files."""
        music_files = []
        scan_path = Path(scan_dir)

        if not scan_path.exists():
            raise FileNotFoundError(f"Scan directory not found: {scan_dir}")

        print(f"Scanning for music files in: {scan_dir}")

        for root, dirs, files in os.walk(scan_path):
            for file in files:
                file_path = Path(root) / file

                # Check if it's a music file
                if file_path.suffix.lower() in MUSIC_EXTENSIONS:
                    music_file = MusicFile(
                        file_path=str(file_path),
                        filename=file_path.name,
                        filename_clean=self._clean_filename(file_path.stem)
                    )
                    music_files.append(music_file)

        print(f"Found {len(music_files)} music files")
        return music_files

    def _clean_filename(self, filename: str) -> str:
        """Clean filename for better matching."""
        # Note: file extension should already be removed by Path.stem,
        # but handle it just in case
        # Only remove if it looks like a file extension (3-4 chars after final dot)
        if '.' in filename:
            parts = filename.rsplit('.', 1)
            if len(parts) == 2 and len(parts[1]) <= 4 and parts[1].isalpha():
                filename = parts[0]

        # Remove common patterns that interfere with matching
        patterns_to_remove = [
            r'\([^)]*\)',  # Remove content in parentheses
            r'\[[^\]]*\]',  # Remove content in brackets
            r'[-_]\d+$',    # Remove trailing track numbers
            r'\s+',         # Multiple spaces to single space
            r'[^\w\s]',     # Remove special characters except spaces
        ]

        for pattern in patterns_to_remove[:-2]:  # Don't remove spaces and special chars yet
            filename = re.sub(pattern, ' ', filename, flags=re.IGNORECASE)

        # Normalize spaces
        filename = re.sub(r'\s+', ' ', filename).strip()

        # Remove special characters (keep spaces for word matching)
        filename = re.sub(r'[^\w\s]', '', filename)

        return filename.lower()

    def _clean_track_info(self, text: str) -> str:
        """Clean track artist/title for matching."""
        if not text:
            return ""

        # Similar cleaning as filename but preserve some structure
        text = re.sub(r'\([^)]*\)', '', text)  # Remove parentheses content
        text = re.sub(r'\[[^\]]*\]', '', text)  # Remove brackets content
        text = re.sub(r'[^\w\s]', '', text)     # Remove special chars
        text = re.sub(r'\s+', ' ', text).strip()  # Normalize spaces

        return text.lower()

    def _calculate_title_similarity(self, track_title_clean: str, filename_clean: str) -> float:
        """Calculate similarity specifically for the title portion."""
        if not track_title_clean:
            return 0.0

        # Direct sequence similarity
        sequence_sim = SequenceMatcher(None, track_title_clean, filename_clean).ratio()

        # Word-based similarity (check if title words appear in filename)
        title_words = set(track_title_clean.split())
        filename_words = set(filename_clean.split())

        if title_words and filename_words:
            # Calculate what percentage of title words are found in filename
            title_word_matches = len(title_words.intersection(filename_words))
            title_word_coverage = title_word_matches / len(title_words) if title_words else 0.0

            # Use the better of the two similarity measures
            return max(sequence_sim, title_word_coverage)

        return sequence_sim

    def _calculate_similarity(self, track: TrackRecord, music_file: MusicFile) -> float:
        """Calculate similarity score between track and music file."""
        # Create search strings
        track_artist_clean = self._clean_track_info(track.artist)
        track_title_clean = self._clean_track_info(track.title)

        # REQUIREMENT: Must have at least partial title match
        if track_title_clean:
            title_similarity = self._calculate_title_similarity(track_title_clean, music_file.filename_clean)
            if title_similarity < 0.3:  # Minimum title similarity threshold
                return 0.0  # No match if title doesn't have partial similarity

        # Try different combinations for matching
        search_patterns = []

        # Artist - Title
        if track_artist_clean and track_title_clean:
            search_patterns.append(f"{track_artist_clean} {track_title_clean}")
            search_patterns.append(f"{track_title_clean} {track_artist_clean}")

        # Just title if artist is empty or very different
        if track_title_clean:
            search_patterns.append(track_title_clean)

        # Just artist if title is empty (but this is now less likely to match due to title requirement)
        if track_artist_clean:
            search_patterns.append(track_artist_clean)

        max_similarity = 0.0

        for pattern in search_patterns:
            if not pattern.strip():
                continue

            similarity = SequenceMatcher(None, pattern, music_file.filename_clean).ratio()

            # Bonus for word matches (even if order is different)
            pattern_words = set(pattern.split())
            filename_words = set(music_file.filename_clean.split())

            if pattern_words and filename_words:
                word_match_ratio = len(pattern_words.intersection(filename_words)) / len(pattern_words.union(filename_words))
                # Combine sequential similarity with word match
                combined_similarity = (similarity * 0.7) + (word_match_ratio * 0.3)
                similarity = max(similarity, combined_similarity)

            max_similarity = max(max_similarity, similarity)

        return max_similarity

    def match_tracks_to_files(self) -> int:
        """Match tracks to music files based on similarity with duplicate resolution."""
        print("Matching tracks to files...")

        # Step 1: Collect all potential matches
        potential_matches = {}  # file_path -> [(track_index, confidence_score)]

        for i, track in enumerate(self.tracks):
            if (i + 1) % 50 == 0:
                print(f"Processed {i + 1}/{len(self.tracks)} tracks...")

            best_match = None
            best_similarity = 0.0

            for music_file in self.music_files:
                similarity = self._calculate_similarity(track, music_file)

                if similarity > best_similarity and similarity >= self.similarity_threshold:
                    best_similarity = similarity
                    best_match = music_file

            if best_match:
                file_path = best_match.file_path
                if file_path not in potential_matches:
                    potential_matches[file_path] = []
                potential_matches[file_path].append((i, best_similarity))

        # Step 2: Resolve duplicates - keep only the highest confidence match for each file
        matched_count = 0
        self.duplicate_files_resolved = 0

        for file_path, matches in potential_matches.items():
            if len(matches) > 1:
                # Multiple tracks matched to the same file - keep only the best one
                matches.sort(key=lambda x: x[1], reverse=True)  # Sort by confidence, highest first
                best_match = matches[0]
                self.duplicate_files_resolved += len(matches) - 1

                # Set the match for the best track only
                track_index, confidence = best_match
                self.tracks[track_index].matched_file_path = file_path
                self.tracks[track_index].confidence_score = confidence
                matched_count += 1
            else:
                # Single match - no conflict
                track_index, confidence = matches[0]
                self.tracks[track_index].matched_file_path = file_path
                self.tracks[track_index].confidence_score = confidence
                matched_count += 1

        duplicate_msg = ""
        if self.duplicate_files_resolved > 0:
            duplicate_msg = f" ({self.duplicate_files_resolved} duplicate file matches resolved)"

        print(f"Successfully matched {matched_count}/{len(self.tracks)} tracks{duplicate_msg}")
        return matched_count

    def export_results(self, output_path: str) -> None:
        """Export results to CSV file (only matched tracks, sorted by confidence)."""
        # Filter to only matched tracks
        matched_tracks = [track for track in self.tracks if track.matched_file_path]

        # Sort by confidence score (highest first) - same order as in the report
        matched_tracks.sort(key=lambda t: t.confidence_score, reverse=True)

        with open(output_path, 'w', encoding='utf-8-sig', newline='') as file:
            writer = csv.writer(file)

            # Write header
            writer.writerow(['rekordboxId', 'artist', 'song title', 'file path'])

            # Write data (only matched tracks, sorted by confidence)
            for track in matched_tracks:
                writer.writerow([
                    track.rekordbox_id,
                    track.artist,
                    track.title,
                    track.matched_file_path
                ])

        print(f"Results exported to: {output_path} ({len(matched_tracks)} matched tracks, sorted by confidence)")

    def print_match_summary(self) -> None:
        """Print a summary of matching results."""
        total_tracks = len(self.tracks)
        matched_tracks = sum(1 for track in self.tracks if track.matched_file_path)
        unmatched_tracks = total_tracks - matched_tracks

        print("\nMatch Summary:")
        print(f"  Total tracks: {total_tracks}")
        print(f"  Matched: {matched_tracks}")
        print(f"  Unmatched: {unmatched_tracks}")
        print(f"  Match rate: {matched_tracks/total_tracks*100:.1f}%")

        if self.duplicate_files_resolved > 0:
            print(f"  Duplicate file matches resolved: {self.duplicate_files_resolved}")

        if unmatched_tracks > 0:
            print(f"\nAll unmatched tracks:")
            for track in self.tracks:
                if not track.matched_file_path:
                    print(f"  - {track.artist} - {track.title} (ID: {track.rekordbox_id})")

    def generate_report(self, report_path: str, csv_path: str, scan_dir: str) -> None:
        """Generate a detailed human-readable report."""
        # Sort matched tracks by confidence score (descending)
        matched_tracks = [track for track in self.tracks if track.matched_file_path]
        unmatched_tracks = [track for track in self.tracks if not track.matched_file_path]

        matched_tracks.sort(key=lambda t: t.confidence_score, reverse=True)

        with open(report_path, 'w', encoding='utf-8') as file:
            # Header
            file.write("# File Path Matcher Report\n")
            file.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # Configuration
            file.write("## Configuration\n")
            file.write(f"- **Input CSV**: {csv_path}\n")
            file.write(f"- **Scan Directory**: {scan_dir}\n")
            file.write(f"- **Similarity Threshold**: {self.similarity_threshold}\n")
            file.write(f"- **Music Files Found**: {len(self.music_files)}\n\n")

            # Summary
            total_tracks = len(self.tracks)
            matched_count = len(matched_tracks)
            unmatched_count = len(unmatched_tracks)

            file.write("## Summary\n")
            file.write(f"- **Total Tracks**: {total_tracks}\n")
            file.write(f"- **Successfully Matched**: {matched_count}\n")
            file.write(f"- **Unmatched**: {unmatched_count}\n")
            file.write(f"- **Match Rate**: {matched_count/total_tracks*100:.1f}%\n")

            if self.duplicate_files_resolved > 0:
                file.write(f"- **Duplicate File Matches Resolved**: {self.duplicate_files_resolved}\n")

            file.write("\n")

            # Confidence distribution
            if matched_tracks:
                high_conf = sum(1 for t in matched_tracks if t.confidence_score >= 0.8)
                med_conf = sum(1 for t in matched_tracks if 0.6 <= t.confidence_score < 0.8)
                low_conf = sum(1 for t in matched_tracks if t.confidence_score < 0.6)

                file.write("## Confidence Distribution\n")
                file.write(f"- **High Confidence** (≥0.8): {high_conf} tracks\n")
                file.write(f"- **Medium Confidence** (0.6-0.8): {med_conf} tracks\n")
                file.write(f"- **Low Confidence** (<0.6): {low_conf} tracks\n\n")

            # Matched tracks (sorted by confidence)
            if matched_tracks:
                file.write("## Matched Tracks (Sorted by Confidence)\n\n")
                for i, track in enumerate(matched_tracks, 1):
                    confidence_bar = "█" * int(track.confidence_score * 10) + "░" * (10 - int(track.confidence_score * 10))
                    file.write(f"### {i}. {track.artist} - {track.title}\n")
                    file.write(f"- **Rekordbox ID**: {track.rekordbox_id}\n")
                    file.write(f"- **Confidence**: {track.confidence_score:.3f} `{confidence_bar}`\n")
                    file.write(f"- **File Path**: `{track.matched_file_path}`\n")
                    file.write(f"- **Streaming**: {track.streaming}\n\n")

            # Unmatched tracks
            if unmatched_tracks:
                file.write("## Unmatched Tracks\n\n")
                file.write(f"The following {len(unmatched_tracks)} tracks could not be matched with local files:\n\n")

                for i, track in enumerate(unmatched_tracks, 1):
                    file.write(f"{i}. **{track.artist} - {track.title}**\n")
                    file.write(f"   - Rekordbox ID: {track.rekordbox_id}\n")
                    file.write(f"   - Streaming: {track.streaming}\n\n")

            # Recommendations
            file.write("## Recommendations\n\n")

            if self.duplicate_files_resolved > 0:
                file.write(f"- **{self.duplicate_files_resolved} duplicate file conflicts resolved**: When multiple tracks matched the same file, only the track with the highest confidence score was kept\n")

            if unmatched_count > 0:
                if unmatched_count / total_tracks > 0.3:
                    file.write("- **High number of unmatched tracks**: Consider lowering the similarity threshold (e.g., --similarity 0.4)\n")
                file.write("- Check that file naming follows 'Artist - Title' or similar patterns\n")
                file.write("- Verify the scan directory contains the expected music files\n")
                file.write("- Consider organizing files in artist/album folders for better matching\n")

            if matched_tracks:
                low_conf_count = sum(1 for t in matched_tracks if t.confidence_score < 0.6)
                if low_conf_count > 0:
                    file.write(f"- **{low_conf_count} low-confidence matches**: Review these matches manually\n")

            file.write("- Remove parentheses, brackets, and version info from filenames for better matching\n")

        print(f"Detailed report saved to: {report_path}")

    def process(self, csv_path: str, scan_dir: str, output_path: str, report_path: Optional[str] = None) -> None:
        """Main processing method.

        Args:
            csv_path: Path to input CSV file with track data
            scan_dir: Directory to scan for music files
            output_path: Path for output CSV file
            report_path: Optional path for detailed markdown report
        """
        # Load tracks from CSV
        self.tracks = self.load_csv_tracks(csv_path)

        # Scan for music files
        self.music_files = self.scan_music_files(scan_dir)

        if not self.music_files:
            print("Warning: No music files found in scan directory")
            return

        # Match tracks to files
        matched_count = self.match_tracks_to_files()

        # Export results
        self.export_results(output_path)

        # Generate report if requested
        if report_path:
            self.generate_report(report_path, csv_path, scan_dir)

        # Print summary
        self.print_match_summary()
