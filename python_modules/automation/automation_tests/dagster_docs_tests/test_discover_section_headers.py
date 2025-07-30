"""Discover all section headers currently used in the Dagster codebase.

This test scans all public symbols to find section headers (lines ending with ':')
and reports which ones are not in our current whitelist.
"""

# Get the actual docstring
from collections import Counter

from automation.dagster_docs.docstring_rules.section_header_rule import ALLOWED_SECTION_HEADERS
from automation.dagster_docs.validator import SymbolImporter, extract_section_headers_from_docstring

from automation_tests.dagster_docs_tests.test_known_valid_symbols import (
    _get_all_dagster_public_symbols,
)


def test_discover_section_headers():
    """Discover all section headers used in public Dagster docstrings."""
    # Use the shared whitelist from the main validation code
    whitelisted_sections = ALLOWED_SECTION_HEADERS

    # Collect all section headers from the codebase
    section_headers = Counter()
    symbols_with_headers = {}  # Track which symbols use which headers

    symbols = _get_all_dagster_public_symbols()
    print(f"Scanning {len(symbols)} public symbols for section headers...")  # noqa: T201

    for symbol_path in symbols:
        try:
            symbol_info = SymbolImporter.import_symbol(symbol_path)
            docstring = symbol_info.docstring

            if not docstring:
                continue

            # Use the shared utility function to extract section headers
            headers = extract_section_headers_from_docstring(docstring)

            # Count each header found and track locations for reporting
            lines = docstring.split("\n")
            for header in headers:
                section_headers[header] += 1

                # Find the line number for this header
                for line_num, line in enumerate(lines, 1):
                    if line.strip() == header:
                        if header not in symbols_with_headers:
                            symbols_with_headers[header] = []
                        symbols_with_headers[header].append(f"{symbol_path}:{line_num}")
                        break
        except Exception:
            # Skip symbols that can't be imported or analyzed
            continue

    # Print results
    print(f"\nFound {len(section_headers)} unique section headers:")  # noqa: T201
    print("=" * 60)  # noqa: T201

    # Sort by frequency (most common first)
    for header, count in section_headers.most_common():
        status = "✓" if header in whitelisted_sections else "✗"
        print(f"{status} {header:<20} ({count:>3} uses)")  # noqa: T201

        # Show a few examples for non-whitelisted headers
        if header not in whitelisted_sections and count <= 5:
            examples = symbols_with_headers[header][:3]  # Show up to 3 examples
            for example in examples:
                print(f"    {example}")  # noqa: T201
            if len(symbols_with_headers[header]) > 3:
                print(f"    ... and {len(symbols_with_headers[header]) - 3} more")  # noqa: T201

    # Summary
    whitelisted_count = sum(
        count for header, count in section_headers.items() if header in whitelisted_sections
    )
    non_whitelisted_count = sum(
        count for header, count in section_headers.items() if header not in whitelisted_sections
    )

    print("\nSummary:")  # noqa: T201
    print(  # noqa: T201
        f"  Whitelisted headers: {len([h for h in section_headers if h in whitelisted_sections])} types, {whitelisted_count} total uses"
    )
    print(  # noqa: T201
        f"  Non-whitelisted headers: {len([h for h in section_headers if h not in whitelisted_sections])} types, {non_whitelisted_count} total uses"
    )

    # Suggest additions to whitelist
    common_non_whitelisted = [
        header
        for header, count in section_headers.most_common()
        if header not in whitelisted_sections and count >= 3
    ]

    if common_non_whitelisted:
        print("\nSuggested additions to whitelist (used 3+ times):")  # noqa: T201
        for header in common_non_whitelisted:
            print(f'    "{header}",')  # noqa: T201

    # This test always passes, it's just for discovery
    assert True


if __name__ == "__main__":
    test_discover_section_headers()
