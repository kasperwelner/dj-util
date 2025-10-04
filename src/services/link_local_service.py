"""LinkLocalService - main orchestration for linking local files."""
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from src.lib.csv_parser import CSVParser, TrackMapping
from src.lib.fuzzy_matcher import FuzzyMatcher
from src.services.rekordbox import RekordboxAdapter
from src.services.audio_converter import AudioConverter, ConversionResult


@dataclass
class LinkResult:
    """Result of linking a single track."""
    track_mapping: TrackMapping
    success: bool
    action: str  # 'updated', 'skipped', 'error', 'converted'
    reason: Optional[str] = None  # Skip/error reason
    db_track_id: Optional[int] = None  # Actual database track ID used
    confidence: Optional[float] = None  # For fuzzy matching
    converted: bool = False  # Was audio conversion performed
    conversion_format: Optional[str] = None  # Target format if converted


class LinkLocalService:
    """Orchestrate the link-local operation."""
    
    def __init__(
        self,
        csv_path: Path,
        rekordbox_adapter: RekordboxAdapter,
        use_fuzzy_match: bool = False,
        match_threshold: float = 0.75,
        dry_run: bool = True,
        strict: bool = False,
        limit: Optional[int] = None,
        allow_mismatch: bool = False,
        force: bool = False,
        convert_format: Optional[str] = None,
        convert_from_formats: Optional[List[str]] = None,
        conversion_output_dir: Optional[Path] = None,
        force_reanalyze: bool = True
    ):
        """Initialize service.
        
        Args:
            csv_path: Path to CSV file
            rekordbox_adapter: Connected Rekordbox adapter
            use_fuzzy_match: Use fuzzy matching instead of IDs
            match_threshold: Similarity threshold for fuzzy matching
            dry_run: Preview changes without writing
            strict: Fail entire operation on first error
            limit: Process only first N rows
            allow_mismatch: Proceed even if artist/title don't match
            force: Update tracks even if already local
            convert_format: Optional target audio format (wav, aiff, flac, mp3, aac, alac)
            convert_from_formats: Optional list of source formats to convert (filters conversion)
            conversion_output_dir: Directory for converted files (defaults to source dir)
            force_reanalyze: Force Rekordbox to re-analyze linked tracks (default: True)
        """
        self.csv_path = csv_path
        self.adapter = rekordbox_adapter
        self.use_fuzzy_match = use_fuzzy_match
        self.match_threshold = match_threshold
        self.dry_run = dry_run
        self.strict = strict
        self.limit = limit
        self.allow_mismatch = allow_mismatch
        self.force = force
        self.convert_format = convert_format
        self.convert_from_formats = convert_from_formats
        self.conversion_output_dir = conversion_output_dir
        self.force_reanalyze = force_reanalyze
        
        # Statistics
        self.total_tracks = 0
        self.updated_count = 0
        self.skipped_count = 0
        self.error_count = 0
        self.converted_count = 0
        self.reanalyzed_count = 0
        
        # For fuzzy matching
        self.fuzzy_matcher: Optional[FuzzyMatcher] = None
        self.streaming_tracks_cache: Optional[List] = None
        
        # Audio converter (lazy init)
        self.audio_converter: Optional[AudioConverter] = None
        if convert_format:
            try:
                self.audio_converter = AudioConverter()
            except RuntimeError as e:
                raise RuntimeError(f"Cannot initialize audio converter: {e}")
    
    def execute(self) -> List[LinkResult]:
        """Execute the link-local operation.
        
        Returns:
            List of LinkResult objects
        """
        results = []
        
        # Parse CSV
        print(f"Reading tracks from {self.csv_path}...")
        parser = CSVParser(require_id=not self.use_fuzzy_match)
        try:
            mappings = parser.parse(str(self.csv_path))
        except Exception as e:
            print(f"✗ Error parsing CSV: {e}")
            return results
        
        self.total_tracks = len(mappings)
        
        # Apply limit if specified
        if self.limit and self.limit < len(mappings):
            mappings = mappings[:self.limit]
            print(f"Limiting to first {self.limit} tracks")
        
        print(f"Found {len(mappings)} tracks to process\n")
        
        # Initialize fuzzy matcher if needed
        if self.use_fuzzy_match:
            self.fuzzy_matcher = FuzzyMatcher(self.match_threshold)
            print("Loading streaming tracks from database...")
            self.streaming_tracks_cache = self.adapter.get_streaming_tracks()
            print(f"Loaded {len(self.streaming_tracks_cache)} streaming tracks\n")
        
        # Backup database if not dry-run
        if not self.dry_run:
            print("Creating database backup...")
            backup_path = self.adapter.backup_database()
            if backup_path:
                print(f"✓ Backup created: {backup_path.name}\n")
            else:
                print(f"✗ Failed to backup database: {self.adapter.error_message}")
                if self.strict:
                    return results
        
        print("Processing tracks...")
        print("=" * 60)
        
        # Process each track
        for i, mapping in enumerate(mappings, 1):
            print(f"\n[{i}/{len(mappings)}] ", end="")
            result = self._process_track(mapping)
            results.append(result)
            
            # Update statistics
            if result.success:
                self.updated_count += 1
            elif result.action == 'skipped':
                self.skipped_count += 1
            else:  # error
                self.error_count += 1
                
                # Fail fast if strict mode
                if self.strict:
                    print(f"\n\n✗ Stopping due to error (strict mode)")
                    break
        
        print("\n" + "=" * 60)
        self._print_summary(results)
        
        return results
    
    def _process_track(self, mapping: TrackMapping) -> LinkResult:
        """Process a single track mapping.
        
        Args:
            mapping: TrackMapping object
            
        Returns:
            LinkResult object
        """
        artist_title = f"{mapping.artist} - {mapping.title}"
        
        # Step 1: Find track in database
        if self.use_fuzzy_match:
            # Fuzzy matching
            match_candidate = self.fuzzy_matcher.find_best_match(
                mapping.artist,
                mapping.title,
                self.streaming_tracks_cache
            )
            
            if not match_candidate:
                print(f"⊘ {artist_title}")
                print(f"   Skipped: No match found (threshold: {self.match_threshold})")
                return LinkResult(
                    track_mapping=mapping,
                    success=False,
                    action='skipped',
                    reason='No match found'
                )
            
            track_id = match_candidate.track_id
            confidence = match_candidate.similarity
            
            # Show match info
            print(f"✓ {artist_title}")
            print(f"   Matched: {match_candidate.artist} - {match_candidate.title} (ID: {track_id}) [confidence: {confidence:.3f}]")
            
            if match_candidate.ambiguous:
                print(f"   ⚠ Ambiguous match detected")
            
            mapping.matched_track_id = track_id
            mapping.match_confidence = confidence
            mapping.match_ambiguous = match_candidate.ambiguous
            
        else:
            # ID-based matching
            if not mapping.rekordbox_id:
                print(f"✗ {artist_title}")
                print(f"   Error: No Rekordbox ID in CSV")
                return LinkResult(
                    track_mapping=mapping,
                    success=False,
                    action='error',
                    reason='No Rekordbox ID'
                )
            
            track_id = mapping.rekordbox_id
            print(f"→ {artist_title}")
        
        # Step 2: Validate track exists
        db_track = self.adapter.get_track_by_id(track_id)
        if not db_track:
            print(f"   ✗ Error: Track ID {track_id} not found in database")
            return LinkResult(
                track_mapping=mapping,
                success=False,
                action='error',
                reason='Track ID not found',
                db_track_id=track_id
            )
        
        # Step 3: Check if already local
        if not db_track.is_streaming and not self.force:
            print(f"   ⊘ Skipped: Already local")
            return LinkResult(
                track_mapping=mapping,
                success=False,
                action='skipped',
                reason='Already local',
                db_track_id=track_id
            )
        
        # Step 4: Check artist/title match (unless allow_mismatch)
        if not self.use_fuzzy_match and not self.allow_mismatch:
            if db_track.artist != mapping.artist or db_track.title != mapping.title:
                print(f"   ⊘ Skipped: Artist/title mismatch")
                print(f"      CSV:      {mapping.artist} - {mapping.title}")
                print(f"      Database: {db_track.artist} - {db_track.title}")
                return LinkResult(
                    track_mapping=mapping,
                    success=False,
                    action='skipped',
                    reason='Artist/title mismatch',
                    db_track_id=track_id
                )
        
        # Step 5: Validate file exists
        if not mapping.file_exists:
            print(f"   ✗ Error: File not found at {mapping.file_path}")
            return LinkResult(
                track_mapping=mapping,
                success=False,
                action='error',
                reason='File not found',
                db_track_id=track_id
            )
        
        # Step 5.5: Audio conversion (if needed)
        file_path_to_use = mapping.normalized_path
        file_size_to_use = mapping.file_size
        converted = False
        conversion_format = None
        
        if self.audio_converter and self.convert_format:
            source_path = Path(mapping.file_path)
            
            # Check if source format matches convert_from filter (if specified)
            should_convert = True
            if self.convert_from_formats:
                source_ext = source_path.suffix.lstrip(".").lower()
                # Normalize aiff/aif
                if source_ext in ("aif", "aiff"):
                    source_ext = "aiff"
                # Normalize m4a/aac
                if source_ext in ("m4a", "aac"):
                    source_ext = "aac"
                
                should_convert = source_ext in self.convert_from_formats
                
                if not should_convert:
                    print(f"   ℹ Skipping conversion (source format {source_ext.upper()} not in filter)")
            
            if should_convert and self.audio_converter.is_conversion_needed(source_path, self.convert_format):
                print(f"   🔄 Converting to {self.convert_format.upper()}...")
                
                if self.dry_run:
                    print(f"      Would convert: {source_path.name} → {source_path.stem}.{self.convert_format}")
                    converted = True
                    conversion_format = self.convert_format
                else:
                    # Perform conversion
                    conv_result = self.audio_converter.convert(
                        source_path=source_path,
                        target_format=self.convert_format,
                        output_dir=self.conversion_output_dir,
                        preserve_original=True,
                        overwrite=False
                    )
                    
                    if conv_result.success:
                        # Use converted file
                        file_path_to_use = str(conv_result.output_path)
                        file_size_to_use = conv_result.output_path.stat().st_size
                        converted = True
                        conversion_format = self.convert_format
                        print(f"      ✓ Converted: {conv_result.output_path.name}")
                    else:
                        # Conversion failed - decide whether to proceed with original
                        print(f"      ⚠ Conversion failed: {conv_result.error_message}")
                        print(f"      → Using original file instead")
            else:
                print(f"   ℹ No conversion needed (already {self.convert_format.upper()})")
        
        # Step 6: Update database (if not dry-run)
        if self.dry_run:
            print(f"   → Would update: {file_path_to_use}")
            if self.force_reanalyze:
                print(f"   → Would mark for re-analysis")
            action = 'converted' if converted else 'updated'
            return LinkResult(
                track_mapping=mapping,
                success=True,
                action=action,
                db_track_id=track_id,
                confidence=mapping.match_confidence,
                converted=converted,
                conversion_format=conversion_format
            )
        else:
            success = self.adapter.update_track_to_local(
                track_id,
                file_path_to_use,
                file_size_to_use
            )
            
            if success:
                print(f"   ✓ Updated: {file_path_to_use}")
                action = 'converted' if converted else 'updated'
                if converted:
                    self.converted_count += 1
                
                # Step 7: Force re-analysis (if enabled)
                if self.force_reanalyze:
                    print(f"   🔄 Marking for re-analysis...")
                    reanalyze_success = self.adapter.force_reanalyze(track_id)
                    if reanalyze_success:
                        print(f"   ✓ Will be re-analyzed when Rekordbox opens")
                        self.reanalyzed_count += 1
                    else:
                        print(f"   ⚠ Could not mark for re-analysis: {self.adapter.error_message}")
                
                return LinkResult(
                    track_mapping=mapping,
                    success=True,
                    action=action,
                    db_track_id=track_id,
                    confidence=mapping.match_confidence,
                    converted=converted,
                    conversion_format=conversion_format
                )
            else:
                print(f"   ✗ Error: {self.adapter.error_message}")
                return LinkResult(
                    track_mapping=mapping,
                    success=False,
                    action='error',
                    reason=self.adapter.error_message,
                    db_track_id=track_id
                )
    
    def _print_summary(self, results: List[LinkResult]):
        """Print summary of results.
        
        Args:
            results: List of LinkResult objects
        """
        print("\nSummary")
        print("-------")
        print(f"Total tracks: {len(results)}")
        print(f"Updated: {self.updated_count}")
        print(f"Skipped: {self.skipped_count}")
        print(f"Errors: {self.error_count}")
        
        if self.converted_count > 0:
            print(f"Converted: {self.converted_count}")
        
        if self.reanalyzed_count > 0:
            print(f"Marked for re-analysis: {self.reanalyzed_count}")
        
        if self.use_fuzzy_match and self.updated_count > 0:
            high_conf = sum(1 for r in results if r.confidence and r.confidence >= 0.9)
            med_conf = sum(1 for r in results if r.confidence and 0.75 <= r.confidence < 0.9)
            print(f"\nMatch quality:")
            print(f"  - High confidence (≥0.90): {high_conf}")
            print(f"  - Medium confidence (0.75-0.89): {med_conf}")
        
        if self.dry_run:
            print(f"\nDatabase updates: NOT APPLIED (dry-run)")
            print(f"Use --apply to execute changes.")
        else:
            print(f"\nDatabase updates: APPLIED")
