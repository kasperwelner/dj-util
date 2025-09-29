"""Export command CLI implementation using Click."""
import sys
from pathlib import Path
from typing import Optional
import click
from src.services.rekordbox import RekordboxAdapter
from src.services.tag_selector import TagSelector
from src.services.csv_exporter import CSVExporter
from src.lib.validators import (
    validate_database_path,
    validate_output_path,
    validate_limit,
    validate_unicode_support
)
from src.lib.progress import (
    ProgressIndicator,
    format_track_count,
    show_spinner
)


@click.command(name='rekordbox-export')
@click.option(
    '--db-path',
    type=click.Path(exists=False),  # We'll validate separately
    help='Path to Rekordbox database (auto-detected if not specified)'
)
@click.option(
    '--output', '-o',
    type=click.Path(),
    default=None,
    help='Output CSV file path (auto-generated from tags if not specified)'
)
@click.option(
    '--limit',
    type=int,
    default=None,
    help='Limit number of tracks exported (for testing)'
)
@click.option(
    '--all-tags',
    is_flag=True,
    help='Export all streaming tracks without tag filtering'
)
@click.option(
    '--tags',
    type=str,
    multiple=True,
    help='Specify tag names to filter (can be used multiple times)'
)
@click.option(
    '--quiet', '-q',
    is_flag=True,
    help='Suppress progress output'
)
def export_command(
    db_path: Optional[str],
    output: str,
    limit: Optional[int],
    all_tags: bool,
    tags: tuple,
    quiet: bool
) -> None:
    """Export streaming tracks from Rekordbox to CSV.
    
    This command connects to your Rekordbox database, allows you to select
    MyTags interactively (or via command line), and exports all streaming
    tracks with those tags to a CSV file.
    
    Examples:
        rekordbox-export
        rekordbox-export --output my_tracks.csv
        rekordbox-export --tags "House" --tags "Techno"
        rekordbox-export --all-tags --limit 100
    """
    # Check Unicode support
    if not quiet and not validate_unicode_support():
        click.echo("Warning: Unicode support may be limited on this system", err=True)
    
    # Validate database path
    is_valid, db_result = validate_database_path(db_path)
    if not is_valid:
        click.echo(f"Error: {db_result}", err=True)
        sys.exit(1)
    
    db_path = db_result
    if not quiet:
        click.echo(f"Using database: {db_path}")
    
    # Output path will be validated after we know the tags (for auto-naming)
    
    # Validate limit
    if limit is not None:
        is_valid, limit_result = validate_limit(limit)
        if not is_valid:
            click.echo(f"Error: {limit_result}", err=True)
            sys.exit(1)
    
    # Initialize services
    rekordbox = RekordboxAdapter()
    selector = TagSelector()
    exporter = CSVExporter()
    
    # Connect to database
    progress = ProgressIndicator("Connecting to Rekordbox database")
    if not quiet:
        progress.start()
    
    if not rekordbox.connect(db_path):
        if not quiet:
            progress.stop(success=False)
        click.echo(f"Error: {rekordbox.error_message}", err=True)
        sys.exit(1)
    
    if not quiet:
        progress.stop(success=True)
    
    try:
        # Get all MyTags
        if not quiet:
            show_spinner("Loading tags", duration=0.5)
        
        all_mytags = rekordbox.get_all_mytags()
        
        if not all_mytags:
            click.echo("No MyTags found in database", err=True)
            sys.exit(1)
        
        if not quiet:
            click.echo(f"Found {len(all_mytags)} tag(s)")
        
        # Determine which tags to use
        selected_tags = []
        
        if all_tags:
            # Export all streaming tracks without filtering
            if not quiet:
                click.echo("Exporting all streaming tracks (no tag filter)")
        elif tags:
            # Use command-line specified tags
            tag_names = set(tags)
            selected_tags = [t for t in all_mytags if t.name in tag_names]
            
            if not selected_tags:
                click.echo(f"Error: No matching tags found for: {', '.join(tags)}", err=True)
                sys.exit(1)
            
            if not quiet:
                click.echo(f"Using {len(selected_tags)} specified tag(s)")
        else:
            # Interactive selection
            selected_tags = selector.select_tags(all_mytags)
            
            if not selected_tags:
                click.echo("No tags selected. Exiting.", err=True)
                sys.exit(0)
            
            if not selector.confirm_selection(selected_tags):
                click.echo("Export cancelled.")
                sys.exit(0)
        
        # Get tracks based on selection
        progress = ProgressIndicator("Loading tracks")
        if not quiet:
            progress.start()
        
        if all_tags or not selected_tags:
            # Get all streaming tracks
            tracks = rekordbox.get_streaming_tracks()
        else:
            # Get tracks with selected tags
            tag_ids = [tag.id for tag in selected_tags]
            tracks = rekordbox.get_streaming_tracks_by_tags(tag_ids)
        
        if not quiet:
            progress.stop(success=True, message=f"Found {format_track_count(len(tracks))}")
        
        if not tracks:
            click.echo("No streaming tracks found with selected tags", err=True)
            sys.exit(1)
        
        # Generate output filename if not specified
        if output is None:
            if all_tags:
                output = exporter.get_default_filename(["all_streaming"])
            elif selected_tags:
                tag_names = [tag.name for tag in selected_tags]
                output = exporter.get_default_filename(tag_names)
            else:
                output = exporter.get_default_filename([])
            
            if not quiet:
                click.echo(f"Output file: {output}")
        
        # Now validate the output path
        is_valid, out_result = validate_output_path(output)
        if not is_valid:
            click.echo(f"Error: {out_result}", err=True)
            sys.exit(1)
        
        if "Warning:" in out_result and not quiet:
            click.echo(out_result)
        
        # Apply limit if specified
        if limit and limit < len(tracks):
            tracks = tracks[:limit]
            if not quiet:
                click.echo(f"Limiting export to {limit} tracks")
        
        # Export to CSV
        progress = ProgressIndicator("Exporting to CSV")
        if not quiet:
            progress.start()
        
        tag_names = [tag.name for tag in selected_tags] if selected_tags else []
        export_result = exporter.export_tracks(tracks, output, tag_names)
        
        if not quiet:
            progress.stop(success=True)
        
        if export_result.file_exists():
            if not quiet:
                click.echo(f"\n✓ Successfully exported {export_result.track_count} tracks to {export_result.file_path}")
        else:
            click.echo(f"Error: Failed to create export file", err=True)
            sys.exit(1)
    
    finally:
        # Clean up
        rekordbox.close()


if __name__ == '__main__':
    export_command()