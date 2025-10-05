"""Bandcamp wishlist CLI command."""
import sys

import click

from services.bandcamp_wishlist import BandcampWishlistAutomator


@click.command(name="bandcamp-wishlist-add")
@click.option(
    "--input-csv",
    "-i",
    type=click.Path(exists=True, dir_okay=False, readable=True),
    required=True,
    help="Input CSV file with track data (id, artist, title columns required)",
)
@click.option(
    "--progress-csv",
    "-p",
    type=click.Path(dir_okay=False, writable=True),
    default="bandcamp_wishlist_progress.csv",
    show_default=True,
    help="Progress CSV file to enable resume support",
)
@click.option(
    "--delay",
    "-d",
    type=float,
    default=2.0,
    show_default=True,
    help="Delay in seconds between processing tracks",
)
def bandcamp_wishlist_add(input_csv: str, progress_csv: str, delay: float):
    """Add tracks from a CSV to your Bandcamp wishlist.

    This command automates adding tracks to your Bandcamp wishlist with progress tracking
    and resume support. If interrupted, simply run the command again to resume from where
    you left off.

    \b
    Examples:
      # Add tracks from an exported CSV
      dj-tool bandcamp-wishlist-add -i my_tracks.csv

      # Use custom progress file and delay
      dj-tool bandcamp-wishlist-add -i tracks.csv -p progress.csv -d 3.0
    """
    # Prompt for credentials
    click.echo("=" * 60)
    click.echo("Bandcamp Wishlist Automator")
    click.echo("=" * 60)

    username = click.prompt("Bandcamp username or email", type=str)
    password = click.prompt("Bandcamp password", hide_input=True)

    if not username or not password:
        click.echo("Error: Username and password are required", err=True)
        sys.exit(1)

    # Initialize automator
    automator = BandcampWishlistAutomator(
        username=username, password=password, delay_between_tracks=delay, progress_csv=progress_csv
    )

    try:
        # Load previous progress
        automator.load_progress()

        # Setup browser
        click.echo("\nInitializing browser...")
        automator.setup_driver()

        # Login
        if not automator.login():
            click.echo("Failed to login. Please check your credentials.", err=True)
            sys.exit(1)

        # Process tracks
        automator.process_csv(input_csv)

    except KeyboardInterrupt:
        click.echo("\n\n⚠ Interrupted by user")
        click.echo(f"Progress has been saved to {progress_csv}")
        click.echo("Run the command again to resume from where you left off.")
        sys.exit(130)

    except Exception as e:
        click.echo(f"\n✗ Unexpected error: {e}", err=True)
        import traceback

        traceback.print_exc()
        sys.exit(1)

    finally:
        automator.cleanup()
        click.echo("\nBrowser closed.")
