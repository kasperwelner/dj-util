"""Main entry point for the DJ Tool CLI."""
import sys

import click
from importlib.metadata import version, PackageNotFoundError

from cli.export_command import export_command
from cli.link_local_command import link_local
from cli.bandcamp_command import bandcamp_wishlist_add
from cli.match_files_command import match_files


def _get_version() -> str:
    """Get the package version."""
    try:
        return version("dj-tool")
    except PackageNotFoundError:
        return "0.1.0-dev"


@click.group()
@click.version_option(version=_get_version(), prog_name='dj-tool')
def cli():
    """DJ Tool Suite for Rekordbox and Bandcamp.

    A comprehensive toolset for managing your Rekordbox library:

    \b
    • Export streaming tracks filtered by tags
    • Link local files to replace streaming tracks
    • Match CSV tracks with local music files
    • Automate Bandcamp wishlist additions
    """
    pass


# Register all commands
cli.add_command(export_command, name="rekordbox-export")
cli.add_command(link_local, name="rekordbox-link-local")
cli.add_command(match_files, name="match-files")
cli.add_command(bandcamp_wishlist_add, name="bandcamp-wishlist-add")


def main():
    """Main entry point for the application."""
    try:
        cli()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        print(f"\nUnexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
