"""Browse scaffold branch diagnostic logs command."""

from pathlib import Path

import click

from automation.scaffold_logs_viewer import serve_logs


@click.command(name="browse-scaffold-branch-logs")
@click.argument("logs_directory", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option("--port", "-p", default=8000, help="Port to serve on (default: 8000)")
@click.option("--host", "-h", default="localhost", help="Host to serve on (default: localhost)")
def browse_scaffold_branch_logs(logs_directory: str, port: int, host: str) -> None:
    """Launch a web server to browse scaffold branch diagnostic logs.

    This command starts a web server that provides a user-friendly interface
    for viewing scaffold branch diagnostic session logs. The web interface
    shows a list of sessions in the sidebar and displays detailed log entries
    in the main content area.

    LOGS_DIRECTORY should contain files matching the pattern:
    scaffold_diagnostics_*.jsonl

    Example:
        dagster-dev browse-scaffold-branch-logs tmp/scaffold-branch-sessions --port 8001
    """
    logs_path = Path(logs_directory)

    # Check if directory contains any scaffold diagnostic files
    scaffold_files = list(logs_path.glob("scaffold_diagnostics_*.jsonl"))
    if not scaffold_files:
        click.echo(f"No scaffold diagnostic files found in {logs_path}")
        click.echo("Expected files matching pattern: scaffold_diagnostics_*.jsonl")
        return

    click.echo(f"Found {len(scaffold_files)} scaffold diagnostic session(s)")
    serve_logs(logs_path, port=port, host=host)
