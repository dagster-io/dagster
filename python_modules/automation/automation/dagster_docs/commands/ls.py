"""List command for dagster-docs."""

import sys

import click

from automation.dagster_docs.public_api_validator import PublicApiValidator
from automation.dagster_docs.public_packages import get_public_dagster_packages
from automation.dagster_docs.validator import SymbolImporter


def _list_package_symbols(package: str) -> None:
    """List all public symbols for a given package.

    Raises:
        ImportError: If the package cannot be imported
    """
    symbols = SymbolImporter.get_all_public_symbols(package)

    for symbol_info in symbols:
        click.echo(symbol_info.dotted_path)


@click.group()
def ls():
    """List packages and symbols."""
    pass


@ls.command()
def packages():
    """Print out all dagster public packages that are introspectable by the docs tool."""
    try:
        packages = get_public_dagster_packages()
        for package in packages:
            click.echo(package.name)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@ls.command()
@click.option("--all", "list_all", is_flag=True, help="Check all symbols")
@click.option("--package", help="Filter down to a particular package")
def symbols(list_all: bool, package: str | None):
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
        # --all option - list all public symbols from all packages
        try:
            from pathlib import Path

            # Find dagster root directory
            dagster_root = Path.cwd()
            while (
                not (dagster_root / "python_modules").exists()
                and dagster_root != dagster_root.parent
            ):
                dagster_root = dagster_root.parent

            if not (dagster_root / "python_modules").exists():
                click.echo("Error: Could not find dagster repository root", err=True)
                sys.exit(1)

            validator = PublicApiValidator(dagster_root)
            public_symbols = validator.find_public_symbols()

            for symbol in public_symbols:
                click.echo(f"{symbol.module_path}.{symbol.symbol_name}")

        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
