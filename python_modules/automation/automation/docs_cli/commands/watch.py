"""Watch command for dagster-docs."""

import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import click

from automation.docstring_lint.validator import DocstringValidator, SymbolImporter
from automation.docstring_lint.watcher import DocstringFileWatcher


def _resolve_symbol_file_path(symbol_path: str, verbose: bool) -> Path:
    """Resolve a symbol to its source file path.

    Returns:
        Path to the symbol's source file

    Raises:
        Exception: If symbol cannot be resolved or file doesn't exist
    """
    symbol_info = SymbolImporter.import_symbol(symbol_path)

    if not symbol_info.file_path:
        raise Exception(f"Cannot determine source file for symbol '{symbol_path}'")

    target_file = Path(symbol_info.file_path)
    if not target_file.exists():
        raise Exception(f"Source file does not exist: {target_file}")

    return target_file


def _create_validation_callback(symbol_path: str, validator: DocstringValidator, verbose: bool):
    """Create a validation callback function for file watching."""

    def validate_and_report() -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        click.echo(f"[{timestamp}] File changed, validating {symbol_path}...")

        try:
            result = validator.validate_symbol_docstring(symbol_path)

            if result.has_errors():
                click.echo("ERRORS:")
                for error in result.errors:
                    click.echo(f"  - {error}")

            if result.has_warnings():
                click.echo("WARNINGS:")
                for warning in result.warnings:
                    click.echo(f"  - {warning}")

            if result.is_valid() and not result.has_warnings():
                click.echo("✓ Docstring is valid!")
            elif result.is_valid():
                click.echo("✓ Docstring is valid (with warnings)")
            else:
                click.echo("✗ Docstring validation failed")

        except Exception as e:
            click.echo(f"Validation error: {e}", err=True)
            if verbose:
                import traceback

                traceback.print_exc()

        click.echo("-" * 50)

    return validate_and_report


def _setup_signal_handlers(watcher: DocstringFileWatcher) -> None:
    """Setup signal handlers for graceful shutdown."""

    def signal_handler(signum, frame):
        click.echo("\nStopping file watcher...")
        watcher.stop_watching()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def _run_file_watcher(watcher: DocstringFileWatcher, verbose: bool) -> None:
    """Run the file watcher and keep the main thread alive.

    Raises:
        Exception: If the watcher encounters an error
    """
    watcher.start_watching()
    # Keep the main thread alive
    while True:
        time.sleep(1)


def _run_symbol_watch_mode(symbol_path: str, validator: DocstringValidator, verbose: bool) -> int:
    """Run the validation in watch mode for a specific symbol, monitoring file changes.

    Returns:
        0 on successful shutdown, 1 on error
    """
    click.echo(f"Setting up watch mode for symbol: {symbol_path}")

    try:
        target_file = _resolve_symbol_file_path(symbol_path, verbose)
        click.echo(f"Watching file: {target_file}")
        if verbose:
            click.echo("Debug mode enabled - will show file system events")
        click.echo("Press Ctrl+C to stop watching\n")
    except Exception as e:
        click.echo(f"Error resolving symbol: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        return 1

    # Create validation callback and run initial validation
    validate_and_report = _create_validation_callback(symbol_path, validator, verbose)
    validate_and_report()

    # Setup file watcher and signal handlers
    watcher = DocstringFileWatcher(target_file, validate_and_report, verbose)
    _setup_signal_handlers(watcher)

    try:
        _run_file_watcher(watcher, verbose)
    except Exception as e:
        click.echo(f"Watch mode error: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        return 1
    finally:
        watcher.stop_watching()

    return 0


@click.group()
def watch():
    """Watch files for changes."""
    pass


@watch.command()
@click.option("--changed", is_flag=True, help="Watches the files currently changed in git")
@click.option("--symbol", help="Targets a particular symbol")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def docstring(changed: bool, symbol: Optional[str], verbose: bool):
    """Watch docstring files for changes and validate them."""
    # Validate that exactly one option is provided
    if not changed and not symbol:
        click.echo("Error: One of --changed or --symbol must be provided", err=True)
        sys.exit(1)

    if changed and symbol:
        click.echo("Error: Cannot use both --changed and --symbol together", err=True)
        sys.exit(1)

    validator = DocstringValidator()

    if symbol:
        # Watch a specific symbol - reuse existing functionality
        exit_code = _run_symbol_watch_mode(symbol, validator, verbose)
        sys.exit(exit_code)

    elif changed:
        # Watch changed files - this functionality is not fully implemented yet
        raise NotImplementedError(
            "Watching changed files functionality not yet fully implemented. "
            "Use --symbol to watch a specific symbol. "
            "Full changed files watching will be implemented in a future PR."
        )
