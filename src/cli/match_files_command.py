"""Match files CLI command."""
import sys

import click

from services.file_path_matcher import FilePathMatcher


@click.command(name="match-files")
@click.option(
    "--input",
    "-i",
    "input_csv",
    type=click.Path(exists=True, dir_okay=False, readable=True),
    required=True,
    help="Input CSV file with rekordbox track data",
)
@click.option(
    "--scan-dir",
    "-s",
    "scan_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    required=True,
    help="Directory to scan recursively for music files",
)
@click.option(
    "--output",
    "-o",
    "output_csv",
    type=click.Path(dir_okay=False, writable=True),
    required=True,
    help="Output CSV file with matched file paths",
)
@click.option(
    "--similarity",
    "-t",
    type=click.FloatRange(0.0, 1.0),
    default=0.6,
    show_default=True,
    help="Similarity threshold for fuzzy matching (0.0-1.0)",
)
@click.option(
    "--report-path",
    "-r",
    "report_path",
    type=click.Path(dir_okay=False, writable=True),
    default=None,
    help="Optional path for detailed Markdown report",
)
def match_files(input_csv: str, scan_dir: str, output_csv: str, similarity: float, report_path: str):
    """Fuzzy-match CSV tracks to local music files.

    This command scans a directory for music files and matches them with tracks from
    a CSV export based on artist and title similarity. The output CSV contains only
    successfully matched tracks with their file paths.

    \b
    Examples:
      # Basic matching
      dj-tool match-files -i tracks.csv -s ~/Music -o matched.csv

      # With custom similarity threshold and detailed report
      dj-tool match-files -i tracks.csv -s ~/Music -o matched.csv \\
          --similarity 0.8 --report-path match_report.md

      # Lower threshold for more matches (may include false positives)
      dj-tool match-files -i tracks.csv -s ~/Music -o matched.csv -t 0.4
    """
    try:
        # Create matcher with specified threshold
        matcher = FilePathMatcher(similarity_threshold=similarity)

        # Process: load, scan, match, export
        matcher.process(csv_path=input_csv, scan_dir=scan_dir, output_path=output_csv, report_path=report_path)

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        import traceback

        traceback.print_exc()
        sys.exit(1)
