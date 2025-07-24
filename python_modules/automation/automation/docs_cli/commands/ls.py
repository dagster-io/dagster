"""List command for dagster-docs."""

import sys
from typing import Optional

import click

from automation.docstring_lint.validator import SymbolImporter


def _list_package_symbols(package: str) -> None:
    """List all public symbols for a given package.

    Raises:
        ImportError: If the package cannot be imported
    """
    importer = SymbolImporter()
    symbols = importer.get_all_public_symbols(package)

    for symbol_info in symbols:
        click.echo(symbol_info.dotted_path)


@click.group()
def ls():
    """List packages and symbols."""
    pass


@ls.command()
def packages():
    """Print out all dagster public packages that are introspectable by the docs tool."""
    # This functionality is not implemented in docstring_linter yet
    raise NotImplementedError(
        "Package discovery functionality not yet implemented. "
        "This will be implemented in a future PR."
    )


@ls.command()
@click.option("--all", "list_all", is_flag=True, help="Check all symbols")
@click.option("--package", help="Filter down to a particular package")
def symbols(list_all: bool, package: Optional[str]):
    """Print out all public symbols exported."""
    if not list_all and not package:
        click.echo("Error: One of --all or --package must be provided", err=True)
        sys.exit(1)

    if package:
        try:
            _list_package_symbols(package)
            sys.exit(0)
        except ImportError as e:
            click.echo(f"Error: Could not import package '{package}': {e}", err=True)
            sys.exit(1)
    else:
        # --all option - this functionality is not implemented yet
        raise NotImplementedError(
            "Global symbol discovery functionality not yet implemented. "
            "This will be implemented in a future PR."
        )
