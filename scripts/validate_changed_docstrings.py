#!/usr/bin/env python3
"""Validate docstrings in uncommitted changed files.

This script finds all Python files with uncommitted changes and validates
all docstrings in those modules using the modular validation framework.

Usage:
    python scripts/validate_changed_docstrings.py
    python scripts/validate_changed_docstrings.py --verbose
"""

import sys
from pathlib import Path

# Add python modules to path to access automation package
DAGSTER_ROOT = Path(__file__).parent.parent
PYTHON_MODULES_PATH = DAGSTER_ROOT / "python_modules"
sys.path.insert(0, str(PYTHON_MODULES_PATH / "automation"))

from automation.docstring_lint.changed_validator import (
    ValidationConfig,
    print_validation_results,
    validate_changed_files,
)
from automation.docstring_lint.file_discovery import git_changed_files
from automation.docstring_lint.path_converters import dagster_path_converter
from automation.docstring_lint.validator import DocstringValidator


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate docstrings in uncommitted changed files")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    # Get changed Python files
    changed_files = git_changed_files(DAGSTER_ROOT)

    if not changed_files:
        print("No uncommitted Python files found.")  # noqa: T201
        return 0

    print(f"Found {len(changed_files)} uncommitted Python files:")  # noqa: T201
    for file_path in changed_files:
        print(f"  {file_path.relative_to(DAGSTER_ROOT)}")  # noqa: T201
    print()  # noqa: T201

    # Configure validation
    config = ValidationConfig(root_path=DAGSTER_ROOT, path_converter=dagster_path_converter)

    # Validate changed files
    validator = DocstringValidator()
    results = validate_changed_files(changed_files, config, validator)

    # Filter out results with no errors or warnings (unless verbose)
    if not args.verbose:
        results = [r for r in results if r.has_errors() or r.has_warnings()]

    if not results:
        print("No symbols with docstrings found in changed files.")  # noqa: T201
        return 0

    # Count total symbols
    all_symbols = set()
    for file_path in changed_files:
        if config.file_filter(file_path):
            module_path = config.path_converter(file_path, config.root_path)
            if module_path:
                from automation.docstring_lint.changed_validator import extract_symbols_from_file

                symbols = extract_symbols_from_file(file_path, module_path)
                all_symbols.update(symbols)

    print(f"Validating {len(all_symbols)} symbols with docstrings...\n")  # noqa: T201

    if args.verbose:
        # Show all symbols being validated
        for file_path in changed_files:
            if config.file_filter(file_path):
                module_path = config.path_converter(file_path, config.root_path)
                if module_path:
                    from automation.docstring_lint.changed_validator import (
                        extract_symbols_from_file,
                    )

                    symbols = extract_symbols_from_file(file_path, module_path)
                    if symbols:
                        print(f"Symbols in {file_path.relative_to(DAGSTER_ROOT)}:")  # noqa: T201
                        for symbol in sorted(symbols, key=lambda s: s.symbol_path):
                            print(f"  {symbol.symbol_path}")  # noqa: T201
        print()  # noqa: T201

    # Print results and get counts
    total_errors, total_warnings = print_validation_results(results, args.verbose)

    print(f"Summary: {total_errors} errors, {total_warnings} warnings")  # noqa: T201

    if total_errors == 0 and total_warnings == 0:
        print("✓ All docstrings are valid!")  # noqa: T201
    elif total_errors == 0:
        print("✓ All docstrings are valid (with warnings)")  # noqa: T201
    else:
        print("✗ Some docstring validations failed")  # noqa: T201

    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
