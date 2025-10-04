"""CLI command for linking local files to Rekordbox streaming tracks."""
import click
import sys
from pathlib import Path
from src.services.rekordbox import RekordboxAdapter
from src.services.link_local_service import LinkLocalService


@click.command(name="link-local")
@click.option(
    '--csv', 'csv_path',
    required=True,
    type=click.Path(exists=True),
    help='CSV file with rekordboxId (or artist/title), and file path'
)
@click.option(
    '--no-id-match',
    is_flag=True,
    default=False,
    help='Use fuzzy artist/title matching instead of IDs'
)
@click.option(
    '--match-threshold',
    type=float,
    default=0.75,
    help='Similarity threshold for fuzzy matching (0.0-1.0, default: 0.75)'
)
@click.option(
    '--dry-run',
    is_flag=True,
    default=True,
    help='Preview changes without executing (default)'
)
@click.option(
    '--apply',
    is_flag=True,
    default=False,
    help='Execute changes (disables dry-run)'
)
@click.option(
    '--strict',
    is_flag=True,
    default=False,
    help='Fail entire operation on first error'
)
@click.option(
    '--limit',
    type=int,
    default=None,
    help='Process only first N rows (useful for testing)'
)
@click.option(
    '--db-path',
    type=click.Path(),
    default=None,
    help='Explicit path to Rekordbox database'
)
@click.option(
    '--allow-mismatch',
    is_flag=True,
    default=False,
    help='Proceed even if artist/title don\'t match database'
)
@click.option(
    '--force',
    is_flag=True,
    default=False,
    help='Update tracks even if already local'
)
@click.option(
    '--convert-to',
    type=click.Choice(['wav', 'aiff', 'flac', 'mp3', 'aac', 'alac'], case_sensitive=False),
    default=None,
    help='Convert audio files to specified format (requires ffmpeg)'
)
@click.option(
    '--convert-from',
    'convert_from',
    multiple=True,
    type=str,
    default=None,
    help='Only convert files with these source formats (e.g., --convert-from mp3 --convert-from aac)'
)
@click.option(
    '--conversion-dir',
    type=click.Path(),
    default=None,
    help='Output directory for converted files (default: same as source)'
)
@click.option(
    '--skip-reanalyze',
    is_flag=True,
    default=False,
    help='Skip forcing Rekordbox to re-analyze linked tracks (re-analysis is automatic by default)'
)
def link_local(
    csv_path,
    no_id_match,
    match_threshold,
    dry_run,
    apply,
    strict,
    limit,
    db_path,
    allow_mismatch,
    force,
    convert_to,
    convert_from,
    conversion_dir,
    skip_reanalyze
):
    """Convert streaming tracks to local file references.
    
    This command updates Rekordbox streaming tracks to reference local files
    by modifying the database to point to files on disk.
    
    By default, linked tracks are marked for re-analysis so Rekordbox will
    regenerate waveforms and beat grids. Use --skip-reanalyze to disable.
    
    Optionally converts audio files to a different format using ffmpeg.
    
    \b
    Examples:
      # Dry-run (preview changes)
      rekordbox link-local --csv matched_tracks.csv
      
      # Apply changes with ID matching
      rekordbox link-local --csv matched_tracks.csv --apply
      
      # Use fuzzy matching (no IDs required)
      rekordbox link-local --csv tracks.csv --no-id-match --apply
      
      # Test with limited rows first
      rekordbox link-local --csv tracks.csv --apply --limit 5
      
      # Convert all files to FLAC
      rekordbox link-local --csv tracks.csv --convert-to flac --apply
      
      # Convert to WAV with output directory
      rekordbox link-local --csv tracks.csv --convert-to wav --conversion-dir ~/Music/Converted --apply
      
      # Convert only MP3 and AAC files to FLAC
      rekordbox link-local --csv tracks.csv --convert-to flac --convert-from mp3 --convert-from aac --apply
    """
    # Validate arguments
    if match_threshold < 0.0 or match_threshold > 1.0:
        click.echo("Error: --match-threshold must be between 0.0 and 1.0", err=True)
        sys.exit(1)
    
    # Validate conversion directory
    if conversion_dir:
        conversion_path = Path(conversion_dir)
        if not conversion_path.exists():
            click.echo(f"Error: Conversion directory does not exist: {conversion_dir}", err=True)
            sys.exit(1)
        if not conversion_path.is_dir():
            click.echo(f"Error: Conversion directory path is not a directory: {conversion_dir}", err=True)
            sys.exit(1)
    
    # Validate convert-from requires convert-to
    if convert_from and not convert_to:
        click.echo("Error: --convert-from requires --convert-to to be specified", err=True)
        sys.exit(1)
    
    # Normalize convert_from to lowercase list
    if convert_from:
        convert_from = [fmt.lower() for fmt in convert_from]
    
    # Determine actual dry-run state
    actual_dry_run = dry_run and not apply
    
    # Print header
    click.echo("=" * 60)
    click.echo("Rekordbox Link Local Files")
    click.echo("=" * 60)
    click.echo(f"CSV: {csv_path}")
    click.echo(f"Mode: {'DRY RUN (preview only)' if actual_dry_run else 'APPLY CHANGES'}")
    
    if no_id_match:
        click.echo(f"Matching: Fuzzy (artist+title, threshold={match_threshold})")
    else:
        click.echo(f"Matching: ID-based")
    
    if limit:
        click.echo(f"Limit: Processing first {limit} rows only")
    
    if convert_to:
        click.echo(f"Audio conversion: {convert_to.upper()}")
        if convert_from:
            click.echo(f"Convert only from: {', '.join(f.upper() for f in convert_from)}")
        if conversion_dir:
            click.echo(f"Conversion output: {conversion_dir}")
    
    if not skip_reanalyze:
        click.echo(f"Force re-analysis: Yes (tracks will be re-analyzed in Rekordbox)")
    else:
        click.echo(f"Force re-analysis: No (skipped)")
    
    click.echo()
    
    # Warn about closing Rekordbox
    if not actual_dry_run:
        click.echo("⚠ IMPORTANT: Please close Rekordbox before continuing!")
        click.echo("   The database must not be locked for writes to work.")
        click.confirm("   Have you closed Rekordbox?", abort=True)
        click.echo()
    
    # Initialize Rekordbox adapter
    adapter = RekordboxAdapter()
    
    click.echo("Connecting to Rekordbox database...")
    if not adapter.connect(db_path):
        click.echo(f"✗ Error: {adapter.error_message}", err=True)
        click.echo()
        click.echo("Common issues:")
        click.echo("  - Rekordbox is still running (close it)")
        click.echo("  - Database file not found (check path)")
        click.echo("  - Insufficient permissions")
        sys.exit(1)
    
    click.echo("✓ Connected to database")
    click.echo()
    
    try:
        # Initialize service
        service = LinkLocalService(
            csv_path=Path(csv_path),
            rekordbox_adapter=adapter,
            use_fuzzy_match=no_id_match,
            match_threshold=match_threshold,
            dry_run=actual_dry_run,
            strict=strict,
            limit=limit,
            allow_mismatch=allow_mismatch,
            force=force,
            convert_format=convert_to,
            convert_from_formats=list(convert_from) if convert_from else None,
            conversion_output_dir=Path(conversion_dir) if conversion_dir else None,
            force_reanalyze=not skip_reanalyze
        )
        
        # Execute
        results = service.execute()
        
        # Exit code based on results
        if strict and service.error_count > 0:
            sys.exit(1)
        elif service.error_count == len(results) and len(results) > 0:
            # All failed
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        click.echo("\n\n⚠ Interrupted by user", err=True)
        sys.exit(130)
    except RuntimeError as e:
        # Catch ffmpeg not found errors
        click.echo(f"\n✗ Error: {e}", err=True)
        if "ffmpeg" in str(e).lower():
            click.echo("\nTo install ffmpeg:")
            click.echo("  macOS:   brew install ffmpeg")
            click.echo("  Linux:   sudo apt-get install ffmpeg")
            click.echo("  Windows: Download from https://ffmpeg.org/download.html")
        sys.exit(1)
    except Exception as e:
        click.echo(f"\n✗ Unexpected error: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        adapter.close()
