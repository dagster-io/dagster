"""Command-line interface for docstring validation."""

import argparse
import sys

from automation.docstring_lint.validator import DocstringValidator, SymbolImporter


def main() -> int:
    """Main entry point for the docstring validation CLI."""
    parser = argparse.ArgumentParser(
        description="Validate Python docstrings using Sphinx parsing pipeline"
    )
    parser.add_argument(
        "symbol_path", help="Dotted path to the Python symbol (e.g., 'dagster.asset')"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument(
        "--all-public",
        action="store_true",
        help="Validate all public symbols in the specified module",
    )

    args = parser.parse_args()

    # Core use case - validate single docstring efficiently
    validator = DocstringValidator()

    try:
        if args.all_public:
            # Batch validation mode
            importer = SymbolImporter()
            symbols = importer.get_all_public_symbols(args.symbol_path)
            print(f"Validating {len(symbols)} public symbols in {args.symbol_path}\n")  # noqa: T201

            total_errors = 0
            total_warnings = 0

            for symbol_info in symbols:
                result = validator.validate_docstring_text(
                    symbol_info.docstring or "", symbol_info.dotted_path
                )

                if result.has_errors() or result.has_warnings():
                    print(f"--- {symbol_info.dotted_path} ---")  # noqa: T201

                    for error in result.errors:
                        print(f"  ERROR: {error}")  # noqa: T201
                        total_errors += 1

                    for warning in result.warnings:
                        print(f"  WARNING: {warning}")  # noqa: T201
                        total_warnings += 1

                    print()  # noqa: T201

            print(f"Summary: {total_errors} errors, {total_warnings} warnings")  # noqa: T201
            return 1 if total_errors > 0 else 0

        else:
            # Single symbol validation (core use case)
            result = validator.validate_symbol_docstring(args.symbol_path)

            print(f"Validating docstring for: {args.symbol_path}")  # noqa: T201

            if result.has_errors():
                print("\nERRORS:")  # noqa: T201
                for error in result.errors:
                    print(f"  - {error}")  # noqa: T201

            if result.has_warnings():
                print("\nWARNINGS:")  # noqa: T201
                for warning in result.warnings:
                    print(f"  - {warning}")  # noqa: T201

            if result.is_valid() and not result.has_warnings():
                print("✓ Docstring is valid!")  # noqa: T201
            elif result.is_valid():
                print("✓ Docstring is valid (with warnings)")  # noqa: T201
            else:
                print("✗ Docstring validation failed")  # noqa: T201

            return 0 if result.is_valid() else 1

    except Exception as e:
        print(f"Error: {e}")  # noqa: T201
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
