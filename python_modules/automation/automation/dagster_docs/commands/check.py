"""Check command for dagster-docs."""

import sys
from pathlib import Path

import click

from automation.dagster_docs.changed_validator import ValidationConfig, validate_changed_files
from automation.dagster_docs.exclude_lists import (
    EXCLUDE_DOCSTRING_ERRORS,
    EXCLUDE_DOCSTRING_WARNINGS,
    EXCLUDE_MISSING_DOCSTRINGS,
    EXCLUDE_MISSING_EXPORT,
    EXCLUDE_MISSING_PUBLIC,
    EXCLUDE_MISSING_RST,
    EXCLUDE_MODULES_FROM_PUBLIC_SCAN,
    EXCLUDE_RST_FILES,
)
from automation.dagster_docs.file_discovery import git_changed_files
from automation.dagster_docs.path_converters import dagster_path_converter
from automation.dagster_docs.public_api_validator import PublicApiValidator
from automation.dagster_docs.public_packages import get_public_module_names
from automation.dagster_docs.validator import (
    SymbolImporter,
    validate_docstring_text,
    validate_symbol_docstring,
)


def _validate_single_symbol(symbol: str, ignore_exclude_lists: bool = False) -> int:
    """Validate a single symbol's docstring and output results.

    Args:
        symbol: The symbol to validate
        ignore_exclude_lists: If True, ignore exclude lists and validate anyway

    Returns:
        0 if validation succeeded, 1 if it failed
    """
    # Check if symbol is in exclude lists (unless we're ignoring them)
    if not ignore_exclude_lists and (
        symbol in EXCLUDE_MISSING_DOCSTRINGS
        or symbol in EXCLUDE_DOCSTRING_ERRORS
        or symbol in EXCLUDE_DOCSTRING_WARNINGS
    ):
        click.echo(f"Symbol '{symbol}' is in the exclude list - skipping validation")
        click.echo("✓ Symbol excluded from validation")
        return 0

    result = validate_symbol_docstring(symbol)

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


def _validate_package_symbols(package: str, ignore_exclude_lists: bool = False) -> int:
    """Validate all symbols in a package and output results.

    Args:
        package: The package to validate
        ignore_exclude_lists: If True, ignore exclude lists and validate all symbols

    Returns:
        0 if validation succeeded, 1 if there were errors
    """
    symbols = SymbolImporter.get_all_public_symbols(package)
    click.echo(f"Validating {len(symbols)} public symbols in {package}\n")

    total_errors = 0
    total_warnings = 0
    excluded_count = 0

    for symbol_info in symbols:
        # Skip symbols in exclude lists (unless we're ignoring them)
        if not ignore_exclude_lists and (
            symbol_info.dotted_path in EXCLUDE_MISSING_DOCSTRINGS
            or symbol_info.dotted_path in EXCLUDE_DOCSTRING_ERRORS
            or symbol_info.dotted_path in EXCLUDE_DOCSTRING_WARNINGS
        ):
            excluded_count += 1
            continue

        result = validate_docstring_text(symbol_info.docstring or "", symbol_info.dotted_path)

        if result.has_errors() or result.has_warnings():
            click.echo(f"--- {symbol_info.dotted_path} ---")

            for error in result.errors:
                click.echo(f"  ERROR: {error}")
                total_errors += 1

            for warning in result.warnings:
                click.echo(f"  WARNING: {warning}")
                total_warnings += 1

            click.echo()

    if excluded_count > 0 and not ignore_exclude_lists:
        click.echo(f"Note: {excluded_count} symbols excluded from validation")
    click.echo(f"Summary: {total_errors} errors, {total_warnings} warnings")
    return 1 if total_errors > 0 else 0


def _validate_all_packages(ignore_exclude_lists: bool = False) -> int:
    """Validate all symbols across all public Dagster packages and output results.

    Args:
        ignore_exclude_lists: If True, ignore exclude lists and validate all symbols

    Returns:
        0 if validation succeeded, 1 if there were errors
    """
    public_modules = get_public_module_names()
    click.echo(f"Validating docstrings across {len(public_modules)} public Dagster packages\n")

    total_errors = 0
    total_warnings = 0
    total_symbols = 0
    total_excluded = 0

    for package in public_modules:
        try:
            symbols = SymbolImporter.get_all_public_symbols(package)
            total_symbols += len(symbols)

            package_errors = 0
            package_warnings = 0
            package_excluded = 0

            for symbol_info in symbols:
                # Skip symbols in exclude lists (unless we're ignoring them)
                if not ignore_exclude_lists and (
                    symbol_info.dotted_path in EXCLUDE_MISSING_DOCSTRINGS
                    or symbol_info.dotted_path in EXCLUDE_DOCSTRING_ERRORS
                    or symbol_info.dotted_path in EXCLUDE_DOCSTRING_WARNINGS
                ):
                    package_excluded += 1
                    total_excluded += 1
                    continue

                result = validate_docstring_text(
                    symbol_info.docstring or "", symbol_info.dotted_path
                )

                if result.has_errors() or result.has_warnings():
                    if package_errors == 0 and package_warnings == 0:
                        # Only print package header when we encounter first issue
                        click.echo(f"=== {package} ===")

                    click.echo(f"--- {symbol_info.dotted_path} ---")

                    for error in result.errors:
                        click.echo(f"  ERROR: {error}")
                        package_errors += 1
                        total_errors += 1

                    for warning in result.warnings:
                        click.echo(f"  WARNING: {warning}")
                        package_warnings += 1
                        total_warnings += 1

                    click.echo()

            if package_errors > 0 or package_warnings > 0:
                click.echo(
                    f"Package {package}: {package_errors} errors, {package_warnings} warnings"
                )
                if package_excluded > 0 and not ignore_exclude_lists:
                    click.echo(f"  ({package_excluded} symbols excluded)")
                click.echo()

        except ImportError as e:
            click.echo(f"Warning: Could not import package '{package}': {e}\n")
            continue

    click.echo(
        f"Overall Summary: {total_symbols} symbols processed across {len(public_modules)} packages"
    )
    if total_excluded > 0 and not ignore_exclude_lists:
        click.echo(f"  {total_excluded} symbols excluded from validation")
    click.echo(f"Total: {total_errors} errors, {total_warnings} warnings")
    return 1 if total_errors > 0 else 0


def _find_dagster_root() -> Path | None:
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


def _find_git_root() -> Path | None:
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


def _validate_changed_files() -> int:
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

    results = validate_changed_files(changed_files, config)

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
@click.option(
    "--ignore-exclude-lists",
    is_flag=True,
    help="Ignore exclude lists and show all docstring issues",
)
def docstrings(
    changed: bool,
    symbol: str | None,
    check_all: bool,
    package: str | None,
    ignore_exclude_lists: bool,
):
    """Validate the docstrings per the existing logic."""
    # Validate that exactly one option is provided
    options_count = sum([changed, bool(symbol), check_all, bool(package)])
    if options_count != 1:
        click.echo(
            "Error: Exactly one of --changed, --symbol, --all, or --package must be provided",
            err=True,
        )
        sys.exit(1)

    # Function-based validation approach

    if symbol:
        try:
            exit_code = _validate_single_symbol(symbol, ignore_exclude_lists)
            sys.exit(exit_code)
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)

    elif package:
        try:
            exit_code = _validate_package_symbols(package, ignore_exclude_lists)
            sys.exit(exit_code)
        except ImportError as e:
            click.echo(f"Error: Could not import package '{package}': {e}", err=True)
            sys.exit(1)

    elif changed:
        try:
            exit_code = _validate_changed_files()
            sys.exit(exit_code)
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)

    elif check_all:
        try:
            exit_code = _validate_all_packages(ignore_exclude_lists)
            sys.exit(exit_code)
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)


@check.command("rst-symbols")
@click.option(
    "--all", "check_all", is_flag=True, help="Check all RST symbols (with exclude lists applied)"
)
@click.option("--package", help="Filter down to a particular package")
def rst_symbols(check_all: bool, package: str | None):
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
def public_symbols(check_all: bool, package: str | None):
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
def exports(check_all: bool, package: str | None):
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


@check.command("exclude-lists")
@click.option(
    "--missing-public",
    "check_missing_public",
    is_flag=True,
    help="Audit EXCLUDE_MISSING_PUBLIC list for symbols that now have @public decorators",
)
@click.option(
    "--missing-rst",
    "check_missing_rst",
    is_flag=True,
    help="Audit EXCLUDE_MISSING_RST list for symbols that now have RST documentation",
)
@click.option(
    "--missing-export",
    "check_missing_export",
    is_flag=True,
    help="Audit EXCLUDE_MISSING_EXPORT list for symbols that are now exported at top-level",
)
def exclude_lists(check_missing_public: bool, check_missing_rst: bool, check_missing_export: bool):
    """Audit exclude lists to ensure entries are still necessary."""
    if not any([check_missing_public, check_missing_rst, check_missing_export]):
        click.echo("Error: Must specify at least one exclude list to check", err=True)
        sys.exit(1)

    dagster_root = _find_dagster_root()
    if dagster_root is None:
        click.echo("Error: Could not find dagster repository root", err=True)
        sys.exit(1)

    try:
        validator = PublicApiValidator(dagster_root)
        exit_codes = []

        if check_missing_public:
            exit_codes.append(_audit_exclude_missing_public(validator))

        if check_missing_rst:
            if exit_codes:  # Add separator if we already printed something
                click.echo("\n" + "=" * 80 + "\n")
            exit_codes.append(_audit_exclude_missing_rst(validator))

        if check_missing_export:
            if exit_codes:  # Add separator if we already printed something
                click.echo("\n" + "=" * 80 + "\n")
            exit_codes.append(_audit_exclude_missing_export(validator))

        # Exit with 1 if any audit found issues, 0 otherwise
        sys.exit(1 if any(exit_codes) else 0)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def _audit_exclude_missing_public(validator: PublicApiValidator) -> int:
    """Audit EXCLUDE_MISSING_PUBLIC list for symbols that now have @public decorators.

    Returns:
        0 if all entries are still valid, 1 if some entries can be removed
    """
    # Get all symbols that have @public decorators
    public_symbols = validator.find_public_symbols(exclude_modules=EXCLUDE_MODULES_FROM_PUBLIC_SCAN)
    public_lookup = {f"{sym.module_path}.{sym.symbol_name}" for sym in public_symbols}

    # Check which symbols in EXCLUDE_MISSING_PUBLIC actually have @public decorators now
    symbols_with_public = []
    for symbol_path in EXCLUDE_MISSING_PUBLIC:
        if symbol_path in public_lookup:
            symbols_with_public.append(symbol_path)

    if not symbols_with_public:
        click.echo(
            "✓ All entries in EXCLUDE_MISSING_PUBLIC are still valid (symbols still missing @public decorators)"
        )
        return 0

    click.echo(
        f"Found {len(symbols_with_public)} symbols in EXCLUDE_MISSING_PUBLIC that now have @public decorators:"
    )
    click.echo("These entries can be removed from the exclude list:")
    click.echo()

    for symbol_path in sorted(symbols_with_public):
        click.echo(f"  {symbol_path}")

    click.echo()
    click.echo("To remove these entries, edit:")
    click.echo("  python_modules/automation/automation/docstring_lint/exclude_lists.py")

    return 1


def _audit_exclude_missing_rst(validator: PublicApiValidator) -> int:
    """Audit EXCLUDE_MISSING_RST list for symbols that now have RST documentation.

    Returns:
        0 if all entries are still valid, 1 if some entries can be removed
    """
    # Get all symbols documented in RST files
    rst_symbols = validator.find_rst_documented_symbols(exclude_files=EXCLUDE_RST_FILES)
    rst_lookup = {f"{sym.module_path}.{sym.symbol_name}" for sym in rst_symbols}

    # Check which symbols in EXCLUDE_MISSING_RST actually have RST documentation now
    symbols_with_rst = []
    for symbol_path in EXCLUDE_MISSING_RST:
        if symbol_path in rst_lookup:
            symbols_with_rst.append(symbol_path)

    if not symbols_with_rst:
        click.echo(
            "✓ All entries in EXCLUDE_MISSING_RST are still valid (symbols still missing RST documentation)"
        )
        return 0

    click.echo(
        f"Found {len(symbols_with_rst)} symbols in EXCLUDE_MISSING_RST that now have RST documentation:"
    )
    click.echo("These entries can be removed from the exclude list:")
    click.echo()

    for symbol_path in sorted(symbols_with_rst):
        click.echo(f"  {symbol_path}")

    click.echo()
    click.echo("To remove these entries, edit:")
    click.echo("  python_modules/automation/automation/docstring_lint/exclude_lists.py")

    return 1


def _audit_exclude_missing_export(validator: PublicApiValidator) -> int:
    """Audit EXCLUDE_MISSING_EXPORT list for symbols that are now exported at top-level.

    Returns:
        0 if all entries are still valid, 1 if some entries can be removed
    """
    # Get all symbols that have @public decorators and check their export status
    public_symbols = validator.find_public_symbols(exclude_modules=EXCLUDE_MODULES_FROM_PUBLIC_SCAN)
    exported_lookup = {
        f"{sym.module_path}.{sym.symbol_name}" for sym in public_symbols if sym.is_exported
    }

    # Check which symbols in EXCLUDE_MISSING_EXPORT are actually exported now
    symbols_with_export = []
    for symbol_path in EXCLUDE_MISSING_EXPORT:
        if symbol_path in exported_lookup:
            symbols_with_export.append(symbol_path)

    if not symbols_with_export:
        click.echo(
            "✓ All entries in EXCLUDE_MISSING_EXPORT are still valid (symbols still not exported at top-level)"
        )
        return 0

    click.echo(
        f"Found {len(symbols_with_export)} symbols in EXCLUDE_MISSING_EXPORT that are now exported at top-level:"
    )
    click.echo("These entries can be removed from the exclude list:")
    click.echo()

    for symbol_path in sorted(symbols_with_export):
        click.echo(f"  {symbol_path}")

    click.echo()
    click.echo("To remove these entries, edit:")
    click.echo("  python_modules/automation/automation/docstring_lint/exclude_lists.py")

    return 1
