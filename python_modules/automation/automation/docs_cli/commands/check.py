"""Check command for dagster-docs."""

import sys
from pathlib import Path
from typing import Optional

import click

from automation.docstring_lint.changed_validator import ValidationConfig, validate_changed_files
from automation.docstring_lint.exclude_lists import (
    EXCLUDE_MISSING_EXPORT,
    EXCLUDE_MISSING_PUBLIC,
    EXCLUDE_MISSING_RST,
    EXCLUDE_MODULES_FROM_PUBLIC_SCAN,
    EXCLUDE_RST_FILES,
)
from automation.docstring_lint.file_discovery import git_changed_files
from automation.docstring_lint.path_converters import dagster_path_converter
from automation.docstring_lint.public_api_validator import PublicApiValidator
from automation.docstring_lint.validator import DocstringValidator, SymbolImporter


def _validate_single_symbol(validator: DocstringValidator, symbol: str) -> int:
    """Validate a single symbol's docstring and output results.

    Returns:
        0 if validation succeeded, 1 if it failed
    """
    result = validator.validate_symbol_docstring(symbol)

    click.echo(f"Validating docstring for: {symbol}")

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


def _validate_package_symbols(validator: DocstringValidator, package: str) -> int:
    """Validate all symbols in a package and output results.

    Returns:
        0 if validation succeeded, 1 if there were errors
    """
    symbols = SymbolImporter.get_all_public_symbols(package)
    click.echo(f"Validating {len(symbols)} public symbols in {package}\n")

    total_errors = 0
    total_warnings = 0

    for symbol_info in symbols:
        result = validator.validate_docstring_text(
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


def _find_dagster_root() -> Optional[Path]:
    """Find the dagster repository root directory.

    Returns:
        Path to dagster root, or None if not found
    """
    root_path = Path.cwd()
    while not (root_path / "python_modules").exists() and root_path != root_path.parent:
        root_path = root_path.parent

    if not (root_path / "python_modules").exists():
        return None

    return root_path


def _find_git_root() -> Optional[Path]:
    """Find the git repository root directory.

    Returns:
        Path to git root, or None if not in a git repository
    """
    root_path = Path.cwd()
    while not (root_path / ".git").exists() and root_path != root_path.parent:
        root_path = root_path.parent

    if not (root_path / ".git").exists():
        return None

    return root_path


def _validate_changed_files(validator: DocstringValidator) -> int:
    """Validate docstrings in changed files and output results.

    Returns:
        0 if validation succeeded, 1 if there were errors, 2 if no git repo found
    """
    root_path = _find_git_root()
    if root_path is None:
        click.echo("Error: Not in a git repository", err=True)
        return 2

    changed_files = git_changed_files(root_path)
    if not changed_files:
        click.echo("No changed Python files found.")
        return 0

    config = ValidationConfig(
        root_path=root_path,
        path_converter=dagster_path_converter,
    )

    results = validate_changed_files(changed_files, config, validator)

    total_errors = 0
    total_warnings = 0

    for result in results:
        if result.has_errors() or result.has_warnings():
            click.echo(f"--- {result.symbol_info.symbol_path} ---")

            for error in result.errors:
                click.echo(f"  ERROR: {error}")
                total_errors += 1

            for warning in result.warnings:
                click.echo(f"  WARNING: {warning}")
                total_warnings += 1

            click.echo()

    click.echo(f"Summary: {total_errors} errors, {total_warnings} warnings")
    return 1 if total_errors > 0 else 0


@click.group()
def check():
    """Check documentation aspects."""
    pass


@check.command()
@click.option("--changed", is_flag=True, help="Filter down to only outstanding changes")
@click.option("--symbol", help="Filter down to a particular symbol")
@click.option("--all", "check_all", is_flag=True, help="Check all docstrings")
@click.option("--package", help="Filter down to a particular package")
def docstrings(changed: bool, symbol: Optional[str], check_all: bool, package: Optional[str]):
    """Validate the docstrings per the existing logic."""
    # Validate that exactly one option is provided
    options_count = sum([changed, bool(symbol), check_all, bool(package)])
    if options_count != 1:
        click.echo(
            "Error: Exactly one of --changed, --symbol, --all, or --package must be provided",
            err=True,
        )
        sys.exit(1)

    validator = DocstringValidator()

    if symbol:
        try:
            exit_code = _validate_single_symbol(validator, symbol)
            sys.exit(exit_code)
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)

    elif package:
        try:
            exit_code = _validate_package_symbols(validator, package)
            sys.exit(exit_code)
        except ImportError as e:
            click.echo(f"Error: Could not import package '{package}': {e}", err=True)
            sys.exit(1)

    elif changed:
        try:
            exit_code = _validate_changed_files(validator)
            sys.exit(exit_code)
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)

    elif check_all:
        # Check all docstrings - this functionality is not implemented yet
        raise NotImplementedError(
            "Global docstring checking functionality not yet implemented. "
            "This will be implemented in a future PR."
        )


@check.command("rst-symbols")
@click.option(
    "--all", "check_all", is_flag=True, help="Check all RST symbols (with exclude lists applied)"
)
@click.option("--package", help="Filter down to a particular package")
def rst_symbols(check_all: bool, package: Optional[str]):
    """Check that all symbols in the .rst files have corresponding top-level exports in libraries marked with @public."""
    # Validate that exactly one option is provided
    if not check_all and not package:
        click.echo("Error: One of --all or --package must be provided", err=True)
        sys.exit(1)

    dagster_root = _find_dagster_root()
    if dagster_root is None:
        click.echo("Error: Could not find dagster repository root", err=True)
        sys.exit(1)

    try:
        validator = PublicApiValidator(dagster_root)

        # Get RST symbols with exclude files applied
        rst_symbols = validator.find_rst_documented_symbols(exclude_files=EXCLUDE_RST_FILES)

        # Get public symbols with exclude modules applied
        public_symbols = validator.find_public_symbols(
            exclude_modules=EXCLUDE_MODULES_FROM_PUBLIC_SCAN
        )

        # Validate that RST symbols have @public decorators with exclude list applied
        issues = validator.validate_rst_has_public(
            rst_symbols, public_symbols, exclude_symbols=EXCLUDE_MISSING_PUBLIC
        )

        if not issues:
            click.echo("✓ All RST documented symbols have @public decorators")
            sys.exit(0)

        click.echo(f"Found {len(issues)} issues:")
        for issue in issues:
            click.echo(
                f"  {issue.issue_type}: {issue.module_path}.{issue.symbol_name} - {issue.details}"
            )

        sys.exit(1)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@check.command("public-symbols")
@click.option(
    "--all",
    "check_all",
    is_flag=True,
    help="Check all @public symbols (with exclude lists applied)",
)
@click.option("--package", help="Filter down to a particular package")
def public_symbols(check_all: bool, package: Optional[str]):
    """Check that all public classes and functions in the codebase have corresponding entries in .rst files and are exported top-level in their respective package."""
    # Validate that exactly one option is provided
    if not check_all and not package:
        click.echo("Error: One of --all or --package must be provided", err=True)
        sys.exit(1)

    dagster_root = _find_dagster_root()
    if dagster_root is None:
        click.echo("Error: Could not find dagster repository root", err=True)
        sys.exit(1)

    try:
        validator = PublicApiValidator(dagster_root)

        # Get public symbols with exclude modules applied
        public_symbols = validator.find_public_symbols(
            exclude_modules=EXCLUDE_MODULES_FROM_PUBLIC_SCAN
        )

        # Get RST symbols with exclude files applied
        rst_symbols = validator.find_rst_documented_symbols(exclude_files=EXCLUDE_RST_FILES)

        # Validate that @public symbols are documented in RST with exclude lists applied
        issues = validator.validate_public_in_rst(
            public_symbols,
            rst_symbols,
            exclude_symbols=EXCLUDE_MISSING_RST.union(EXCLUDE_MISSING_EXPORT),
        )

        if not issues:
            click.echo("✓ All @public symbols are documented in RST and exported top-level")
            sys.exit(0)

        click.echo(f"Found {len(issues)} issues:")
        for issue in issues:
            click.echo(
                f"  {issue.issue_type}: {issue.module_path}.{issue.symbol_name} - {issue.details}"
            )

        sys.exit(1)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@check.command()
@click.option(
    "--all", "check_all", is_flag=True, help="Check all exports (with exclude lists applied)"
)
@click.option("--package", help="Filter down to a particular package")
def exports(check_all: bool, package: Optional[str]):
    """Check that top-level exports in packages have public decorators and entries in .rst."""
    # Validate that exactly one option is provided
    if not check_all and not package:
        click.echo("Error: One of --all or --package must be provided", err=True)
        sys.exit(1)

    dagster_root = _find_dagster_root()
    if dagster_root is None:
        click.echo("Error: Could not find dagster repository root", err=True)
        sys.exit(1)

    try:
        validator = PublicApiValidator(dagster_root)

        # Get public symbols with exclude modules applied
        public_symbols = validator.find_public_symbols(
            exclude_modules=EXCLUDE_MODULES_FROM_PUBLIC_SCAN
        )

        # Get RST symbols with exclude files applied
        rst_symbols = validator.find_rst_documented_symbols(exclude_files=EXCLUDE_RST_FILES)

        # Validate both directions with exclude lists applied
        public_issues = validator.validate_public_in_rst(
            public_symbols,
            rst_symbols,
            exclude_symbols=EXCLUDE_MISSING_RST.union(EXCLUDE_MISSING_EXPORT),
        )
        rst_issues = validator.validate_rst_has_public(
            rst_symbols, public_symbols, exclude_symbols=EXCLUDE_MISSING_PUBLIC
        )

        all_issues = public_issues + rst_issues

        if not all_issues:
            click.echo("✓ All exports are properly documented and decorated")
            sys.exit(0)

        click.echo(f"Found {len(all_issues)} issues:")
        for issue in all_issues:
            click.echo(
                f"  {issue.issue_type}: {issue.module_path}.{issue.symbol_name} - {issue.details}"
            )

        sys.exit(1)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
