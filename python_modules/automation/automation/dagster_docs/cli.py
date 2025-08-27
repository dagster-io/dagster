"""Command-line interface for docstring validation."""

import signal
import sys
import time
from datetime import datetime
from pathlib import Path

import click

from automation.dagster_docs.validator import (
    SymbolImporter,
    validate_docstring_text,
    validate_symbol_docstring,
)
from automation.dagster_docs.watcher import DocstringFileWatcher


@click.command()
@click.argument("symbol_path")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option(
    "--all-public",
    is_flag=True,
    help="Validate all top-level exported symbols in the specified module",
)
@click.option(
    "--public-methods",
    is_flag=True,
    help="Validate all @public-annotated methods on top-level exported classes in the specified module",
)
@click.option(
    "--watch",
    is_flag=True,
    help="Watch the file containing the symbol for changes and re-validate automatically",
)
def main(
    symbol_path: str, verbose: bool, all_public: bool, public_methods: bool, watch: bool
) -> int:
    """Validate Python docstrings using Sphinx parsing pipeline.

    SYMBOL_PATH: Dotted path to the Python symbol (e.g., 'dagster.asset')
    """
    # Validate argument combinations
    if watch and (all_public or public_methods):
        click.echo("Error: --watch cannot be used with --all-public or --public-methods", err=True)
        return 1

    if all_public and public_methods:
        click.echo("Error: --all-public and --public-methods cannot be used together", err=True)
        return 1

    # Core use case - validate single docstring efficiently
    # Function-based validation approach

    try:
        if watch:
            return _run_watch_mode(symbol_path, verbose)
        elif all_public:
            # Batch validation mode for all top-level exported symbols
            symbols = SymbolImporter.get_all_exported_symbols(symbol_path)
            click.echo(f"Validating {len(symbols)} public symbols in {symbol_path}\n")

            total_errors = 0
            total_warnings = 0

            for symbol_info in symbols:
                result = validate_docstring_text(
                    symbol_info.docstring or "", symbol_info.dotted_path
                )

                if result.has_errors() or result.has_warnings():
                    click.echo(f"--- {symbol_info.dotted_path} ---")

                    for error in result.errors:
                        click.echo(f"  ERROR: {error}")
                        total_errors += 1

                    for warning in result.warnings:
                        click.echo(f"  WARNING: {warning}")
                        total_warnings += 1

                    click.echo()

            click.echo(f"Summary: {total_errors} errors, {total_warnings} warnings")
            return 1 if total_errors > 0 else 0

        elif public_methods:
            # Batch validation mode for @public-annotated methods on top-level exported classes
            methods = SymbolImporter.get_all_public_annotated_methods(symbol_path)
            click.echo(
                f"Validating {len(methods)} @public-annotated methods on top-level exported classes in {symbol_path}\n"
            )

            total_errors = 0
            total_warnings = 0

            for method_info in methods:
                result = validate_docstring_text(
                    method_info.docstring or "", method_info.dotted_path
                )

                if result.has_errors() or result.has_warnings():
                    click.echo(f"--- {method_info.dotted_path} ---")

                    for error in result.errors:
                        click.echo(f"  ERROR: {error}")
                        total_errors += 1

                    for warning in result.warnings:
                        click.echo(f"  WARNING: {warning}")
                        total_warnings += 1

                    click.echo()

            click.echo(f"Summary: {total_errors} errors, {total_warnings} warnings")
            return 1 if total_errors > 0 else 0

        else:
            # Single symbol validation (core use case)
            result = validate_symbol_docstring(symbol_path)

            click.echo(f"Validating docstring for: {symbol_path}")

            if result.has_errors():
                click.echo("\nERRORS:")
                for error in result.errors:
                    click.echo(f"  - {error}")

            if result.has_warnings():
                click.echo("\nWARNINGS:")
                for warning in result.warnings:
                    click.echo(f"  - {warning}")

            if result.is_valid() and not result.has_warnings():
                click.echo("✓ Docstring is valid!")
            elif result.is_valid():
                click.echo("✓ Docstring is valid (with warnings)")
            else:
                click.echo("✗ Docstring validation failed")

            return 0 if result.is_valid() else 1

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        return 1


def _run_watch_mode(symbol_path: str, verbose: bool) -> int:
    """Run the validation in watch mode, monitoring file changes."""
    click.echo(f"Setting up watch mode for symbol: {symbol_path}")

    # First, resolve the symbol to get its file path
    try:
        symbol_info = SymbolImporter.import_symbol(symbol_path)

        if not symbol_info.file_path:
            click.echo(f"Error: Cannot determine source file for symbol '{symbol_path}'", err=True)
            return 1

        target_file = Path(symbol_info.file_path)
        if not target_file.exists():
            click.echo(f"Error: Source file does not exist: {target_file}", err=True)
            return 1

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

    # Define validation callback
    def validate_and_report() -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        click.echo(f"[{timestamp}] File changed, validating {symbol_path}...")

        try:
            result = validate_symbol_docstring(symbol_path)

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

    # Run initial validation
    validate_and_report()

    # Setup file watcher
    watcher = DocstringFileWatcher(target_file, validate_and_report, verbose)

    # Setup signal handler for graceful shutdown
    def signal_handler(signum, frame):
        click.echo("\nStopping file watcher...")
        watcher.stop_watching()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        watcher.start_watching()
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except Exception as e:
        click.echo(f"Watch mode error: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        return 1
    finally:
        watcher.stop_watching()

    return 0


if __name__ == "__main__":
    sys.exit(main())
