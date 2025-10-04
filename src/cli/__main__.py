"""Main entry point for the Rekordbox export CLI."""
import sys
import click
from src.cli.export_command import export_command
from src.cli.link_local_command import link_local


@click.group()
@click.version_option(version='1.0.0', prog_name='rekordbox-tools')
def cli():
    """Rekordbox tools for managing and exporting your music library."""
    pass


# Add commands to the CLI group
cli.add_command(export_command)
cli.add_command(link_local)


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