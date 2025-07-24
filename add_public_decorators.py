#!/usr/bin/env python3
"""Script to add @public decorators to symbols listed in EXCLUDE_MISSING_PUBLIC.

This script:
1. Reads the EXCLUDE_MISSING_PUBLIC set from the exclude lists file
2. For each symbol, finds its definition in the codebase
3. Adds the @public decorator and import statement
4. Uses ruff to clean up imports and formatting
"""

import re
import subprocess

# Import the exclude list
import sys
from pathlib import Path
from typing import Optional

import click

sys.path.insert(
    0,
    "/Users/schrockn/code/dagster/python_modules/automation/automation_tests/docstring_lint_tests",
)
from exclude_lists import EXCLUDE_MISSING_PUBLIC


def find_symbol_definition(symbol_path: str, dagster_root: Path) -> Optional[tuple[Path, int]]:
    """Find the file and line number where a symbol is defined.

    Args:
        symbol_path: Full dotted path like 'dagster.BetaWarning'
        dagster_root: Root directory of the dagster repo

    Returns:
        Tuple of (file_path, line_number) if found, None otherwise
    """
    parts = symbol_path.split(".")
    module_parts = parts[:-1]  # All but the last part
    symbol_name = parts[-1]  # The actual symbol name

    # Try to find the module file
    possible_paths = []

    # For dagster.* symbols, look in python_modules/dagster/dagster/
    if module_parts[0] == "dagster" and len(module_parts) == 1:
        # Top-level dagster symbol - look in __init__.py or main modules
        dagster_dir = dagster_root / "python_modules" / "dagster" / "dagster"
        possible_paths.extend(
            [
                dagster_dir / "__init__.py",
                dagster_dir / "_core" / "definitions" / "__init__.py",
                dagster_dir / "_core" / "__init__.py",
            ]
        )

        # Also search for files that might contain the symbol
        for py_file in dagster_dir.rglob("*.py"):
            if py_file.name != "__init__.py":
                possible_paths.append(py_file)

    # For dagster_* library symbols
    elif module_parts[0].startswith("dagster_"):
        lib_name = module_parts[0]
        lib_dir = dagster_root / "python_modules" / "libraries" / lib_name / lib_name
        if lib_dir.exists():
            possible_paths.extend(
                [
                    lib_dir / "__init__.py",
                ]
            )
            # Add all Python files in the library
            for py_file in lib_dir.rglob("*.py"):
                possible_paths.append(py_file)

    # For dagstermill
    elif module_parts[0] == "dagstermill":
        mill_dir = dagster_root / "python_modules" / "libraries" / "dagstermill" / "dagstermill"
        if mill_dir.exists():
            for py_file in mill_dir.rglob("*.py"):
                possible_paths.append(py_file)

    # Search through possible files
    for file_path in possible_paths:
        if file_path.exists():
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                # Look for class/function definitions
                patterns = [
                    rf"^class {re.escape(symbol_name)}\b",
                    rf"^def {re.escape(symbol_name)}\b",
                    rf"^{re.escape(symbol_name)} = ",
                    rf"^async def {re.escape(symbol_name)}\b",
                ]

                lines = content.split("\n")
                for i, line in enumerate(lines, 1):
                    for pattern in patterns:
                        if re.match(pattern, line.strip()):
                            return (file_path, i)

            except Exception as e:
                click.echo(f"Error reading {file_path}: {e}")
                continue

    return None


def has_public_decorator(file_path: Path, line_number: int) -> bool:
    """Check if a symbol already has @public decorator."""
    try:
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()

        # Look backwards from the symbol definition for @public
        for i in range(max(0, line_number - 10), line_number):
            if i < len(lines) and "@public" in lines[i]:
                return True
        return False
    except Exception:
        return False


def has_public_import(file_path: Path) -> bool:
    """Check if file already imports public from dagster._annotations."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Look for existing import
        patterns = [
            r"from dagster\._annotations import.*public",
            r"from dagster\._annotations import public",
            r"import.*dagster\._annotations.*public",
        ]

        for pattern in patterns:
            if re.search(pattern, content):
                return True
        return False
    except Exception:
        return False


def add_public_decorator(file_path: Path, symbol_name: str, line_number: int) -> bool:
    """Add @public decorator to a symbol definition.

    Args:
        file_path: Path to the file containing the symbol
        symbol_name: Name of the symbol to decorate
        line_number: Line number where the symbol is defined

    Returns:
        True if successful, False otherwise
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()

        # Check if already has @public
        if has_public_decorator(file_path, line_number):
            click.echo("  Already has @public decorator")
            return True

        # Check if this is a variable assignment (can't be decorated)
        symbol_line = lines[line_number - 1].strip()
        if re.match(rf"^{re.escape(symbol_name)}\s*=", symbol_line):
            click.echo(f"  Skipping variable assignment: {symbol_name}")
            return False

        # Add import if not present
        if not has_public_import(file_path):
            # Find the import section (after module docstring, before any code)
            import_insert_line = 0
            in_docstring = False
            docstring_quotes = None

            for i, line in enumerate(lines):
                stripped = line.strip()
                # Handle docstrings
                if not in_docstring and (stripped.startswith('"""') or stripped.startswith("'''")):
                    docstring_quotes = stripped[:3]
                    in_docstring = True
                    if stripped.count(docstring_quotes) >= 2:  # Single line docstring
                        in_docstring = False
                elif in_docstring and docstring_quotes in stripped:
                    in_docstring = False
                elif not in_docstring and (
                    stripped.startswith("from ") or stripped.startswith("import ")
                ):
                    import_insert_line = i + 1
                elif not in_docstring and stripped and not stripped.startswith("#"):
                    break

            lines.insert(import_insert_line, "from dagster._annotations import public\n")
            line_number += 1  # Adjust line number after insertion

        # Find the right place to insert @public (accounting for other decorators)
        insert_line = line_number - 1  # Convert to 0-based indexing

        # Look backwards to find where decorators start
        while insert_line > 0 and lines[insert_line - 1].strip().startswith("@"):
            insert_line -= 1

        # Get the indentation of the symbol definition
        symbol_line = lines[line_number - 1]
        indent = len(symbol_line) - len(symbol_line.lstrip())
        indentation = " " * indent

        # Add @public decorator
        lines.insert(insert_line, f"{indentation}@public\n")

        # Write back to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        click.echo("  Added @public decorator")
        return True

    except Exception as e:
        click.echo(f"  Error adding decorator: {e}")
        return False


def main():
    """Process all symbols in EXCLUDE_MISSING_PUBLIC."""
    dagster_root = Path("/Users/schrockn/code/dagster")

    click.echo(f"Processing {len(EXCLUDE_MISSING_PUBLIC)} symbols...")

    success_count = 0
    not_found_count = 0
    error_count = 0

    for symbol_path in sorted(EXCLUDE_MISSING_PUBLIC):
        click.echo(f"\nProcessing: {symbol_path}")

        # Find the symbol definition
        result = find_symbol_definition(symbol_path, dagster_root)
        if result is None:
            click.echo("  Symbol not found")
            not_found_count += 1
            continue

        file_path, line_number = result
        symbol_name = symbol_path.split(".")[-1]

        click.echo(f"  Found in: {file_path}:{line_number}")

        # Add @public decorator
        if add_public_decorator(file_path, symbol_name, line_number):
            success_count += 1
        else:
            error_count += 1

    click.echo("\n=== Summary ===")
    click.echo(f"Successfully processed: {success_count}")
    click.echo(f"Not found: {not_found_count}")
    click.echo(f"Errors: {error_count}")
    click.echo(f"Total: {len(EXCLUDE_MISSING_PUBLIC)}")

    if success_count > 0:
        click.echo("\nRunning ruff to clean up imports and formatting...")
        try:
            subprocess.run(["make", "ruff"], cwd=dagster_root, check=True)
            click.echo("Ruff completed successfully")
        except subprocess.CalledProcessError as e:
            click.echo(f"Ruff failed: {e}")


if __name__ == "__main__":
    main()
