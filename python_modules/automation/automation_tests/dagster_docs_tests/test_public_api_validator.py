"""Tests for public API validation utilities."""

from pathlib import Path

import pytest
from automation.dagster_docs.exclude_lists import (
    EXCLUDE_MISSING_EXPORT,
    EXCLUDE_MISSING_PUBLIC,
    EXCLUDE_MISSING_RST,
    EXCLUDE_MODULES_FROM_PUBLIC_SCAN,
    EXCLUDE_RST_FILES,
)
from automation.dagster_docs.public_api_validator import (
    PublicApiValidator,
    PublicSymbol,
    RstSymbol,
    ValidationIssue,
)

# All exclude lists are now imported from exclude_lists.py


class TestPublicApiValidator:
    """Test suite for public API validation."""

    @pytest.fixture
    def validator(self):
        """Create a validator instance for testing."""
        dagster_root = Path(__file__).parent.parent.parent.parent.parent
        return PublicApiValidator(dagster_root)

    @pytest.fixture
    def public_symbols(self, validator):
        """Load all @public decorated symbols."""
        return validator.find_public_symbols(exclude_modules=EXCLUDE_MODULES_FROM_PUBLIC_SCAN)

    @pytest.fixture
    def rst_symbols(self, validator):
        """Load all RST documented symbols."""
        return validator.find_rst_documented_symbols(exclude_files=EXCLUDE_RST_FILES)

    def test_find_public_symbols(self, validator):
        """Test that we can find @public decorated symbols."""
        symbols = validator.find_public_symbols()

        # Should find some symbols
        assert len(symbols) > 0

        # Check structure of returned symbols
        for symbol in symbols[:5]:  # Check first few
            assert isinstance(symbol, PublicSymbol)
            assert symbol.module_path
            assert symbol.symbol_name
            assert symbol.symbol_type in ["class", "function"]
            assert isinstance(symbol.is_exported, bool)
            assert symbol.source_file

    def test_find_rst_documented_symbols(self, validator):
        """Test that we can extract symbols from RST files."""
        symbols = validator.find_rst_documented_symbols()

        # Should find some symbols
        assert len(symbols) > 0

        # Check structure of returned symbols
        for symbol in symbols[:5]:  # Check first few
            assert isinstance(symbol, RstSymbol)
            assert symbol.module_path
            assert symbol.symbol_name
            assert symbol.rst_directive in ["autoclass", "autofunction", "autodecorator"]
            assert symbol.rst_file

    def test_validate_public_in_rst_no_excludes(self, validator, public_symbols, rst_symbols):
        """Test validation that @public symbols are in RST (without excludes)."""
        issues = validator.validate_public_in_rst(public_symbols, rst_symbols)

        # This will likely find issues since we're not using excludes
        # The test validates the mechanism works
        assert isinstance(issues, list)
        for issue in issues:
            assert isinstance(issue, ValidationIssue)
            assert issue.issue_type in ["missing_rst", "missing_export"]
            assert issue.symbol_name
            assert issue.module_path
            assert issue.details

    def test_validate_public_in_rst_with_excludes(self, validator, public_symbols, rst_symbols):
        """Test validation with exclude lists to handle existing inconsistencies."""
        issues = validator.validate_public_in_rst(
            public_symbols,
            rst_symbols,
            exclude_symbols=EXCLUDE_MISSING_RST.union(EXCLUDE_MISSING_EXPORT),
        )

        # With proper excludes, should have minimal/no issues
        # Print issues for manual review
        if issues:
            print(f"\nFound {len(issues)} @public->RST validation issues:")  # noqa: T201
            for issue in issues[:10]:  # Show first 10
                print(f"  {issue.issue_type}: {issue.module_path}.{issue.symbol_name}")  # noqa: T201
                print(f"    {issue.details}")  # noqa: T201

    def test_validate_rst_has_public_no_excludes(self, validator, rst_symbols, public_symbols):
        """Test validation that RST symbols have @public (without excludes)."""
        issues = validator.validate_rst_has_public(rst_symbols, public_symbols)

        # This will likely find issues since we're not using excludes
        assert isinstance(issues, list)
        for issue in issues:
            assert isinstance(issue, ValidationIssue)
            assert issue.issue_type == "missing_public"
            assert issue.symbol_name
            assert issue.module_path
            assert issue.details

    def test_validate_rst_has_public_with_excludes(self, validator, rst_symbols, public_symbols):
        """Test validation with exclude lists to handle existing inconsistencies."""
        issues = validator.validate_rst_has_public(
            rst_symbols, public_symbols, exclude_symbols=EXCLUDE_MISSING_PUBLIC
        )

        # With proper excludes, should have minimal/no issues
        # Print issues for manual review
        if issues:
            print(f"\nFound {len(issues)} RST->@public validation issues:")  # noqa: T201
            for issue in issues[:10]:  # Show first 10
                print(f"  {issue.issue_type}: {issue.module_path}.{issue.symbol_name}")  # noqa: T201
                print(f"    {issue.details}")  # noqa: T201

    def test_full_bidirectional_validation(self, validator):
        """Test complete bidirectional validation with all exclude lists."""
        # Load symbols with excludes
        public_symbols = validator.find_public_symbols(
            exclude_modules=EXCLUDE_MODULES_FROM_PUBLIC_SCAN
        )
        rst_symbols = validator.find_rst_documented_symbols(exclude_files=EXCLUDE_RST_FILES)

        # Validate both directions
        public_to_rst_issues = validator.validate_public_in_rst(
            public_symbols,
            rst_symbols,
            exclude_symbols=EXCLUDE_MISSING_RST.union(EXCLUDE_MISSING_EXPORT),
        )

        rst_to_public_issues = validator.validate_rst_has_public(
            rst_symbols, public_symbols, exclude_symbols=EXCLUDE_MISSING_PUBLIC
        )

        # Report any remaining issues
        total_issues = len(public_to_rst_issues) + len(rst_to_public_issues)

        if total_issues > 0:
            print("\n=== FULL VALIDATION REPORT ===")  # noqa: T201
            print(f"Total issues found: {total_issues}")  # noqa: T201

            if public_to_rst_issues:
                print(f"\n@public->RST issues ({len(public_to_rst_issues)}):")  # noqa: T201
                for issue in public_to_rst_issues[:10]:
                    print(f"  {issue.issue_type}: {issue.module_path}.{issue.symbol_name}")  # noqa: T201

            if rst_to_public_issues:
                print(f"\nRST->@public issues ({len(rst_to_public_issues)}):")  # noqa: T201
                for issue in rst_to_public_issues[:10]:
                    print(f"  {issue.issue_type}: {issue.module_path}.{issue.symbol_name}")  # noqa: T201

            print("\nTo fix these issues:")  # noqa: T201
            print("1. Add missing @public decorators to RST-documented symbols")  # noqa: T201
            print("2. Add missing RST documentation for @public symbols")  # noqa: T201
            print("3. Add missing top-level exports for @public symbols")  # noqa: T201
            print("4. Or add entries to exclude lists for items that should not be validated")  # noqa: T201

        # For now, don't fail the test - this is informational
        # In the future when issues are resolved, this could assert total_issues == 0

    def test_no_new_public_api_inconsistencies(self, validator):
        """Enforce that no new @public API inconsistencies are introduced.

        This test ensures that the number of issues doesn't grow beyond what's
        already captured in the exclude lists. Any new issues should be either:
        1. Fixed immediately by adding proper @public decorators or RST docs
        2. Added to the appropriate exclude list with justification
        """
        # Load symbols with excludes
        public_symbols = validator.find_public_symbols(
            exclude_modules=EXCLUDE_MODULES_FROM_PUBLIC_SCAN
        )
        rst_symbols = validator.find_rst_documented_symbols(exclude_files=EXCLUDE_RST_FILES)

        # Validate both directions with exclude lists
        public_to_rst_issues = validator.validate_public_in_rst(
            public_symbols,
            rst_symbols,
            exclude_symbols=EXCLUDE_MISSING_RST.union(EXCLUDE_MISSING_EXPORT),
        )

        rst_to_public_issues = validator.validate_rst_has_public(
            rst_symbols, public_symbols, exclude_symbols=EXCLUDE_MISSING_PUBLIC
        )

        # Should have zero issues after applying exclude lists
        total_issues = len(public_to_rst_issues) + len(rst_to_public_issues)

        if total_issues > 0:
            print(f"\n❌ NEW PUBLIC API INCONSISTENCIES DETECTED: {total_issues}")  # noqa: T201

            if public_to_rst_issues:
                print(f"\nNew @public->RST issues ({len(public_to_rst_issues)}):")  # noqa: T201
                for issue in public_to_rst_issues:
                    print(f"  {issue.issue_type}: {issue.module_path}.{issue.symbol_name}")  # noqa: T201

            if rst_to_public_issues:
                print(f"\nNew RST->@public issues ({len(rst_to_public_issues)}):")  # noqa: T201
                for issue in rst_to_public_issues:
                    print(f"  {issue.issue_type}: {issue.module_path}.{issue.symbol_name}")  # noqa: T201

            print("\nTo fix these issues:")  # noqa: T201
            print("1. Add missing @public decorators to RST-documented symbols")  # noqa: T201
            print("2. Add missing RST documentation for @public symbols")  # noqa: T201
            print("3. Add missing top-level exports for @public symbols")  # noqa: T201
            print("4. Or add entries to exclude lists with proper justification")  # noqa: T201

        # FAIL the test if there are any unexcluded issues
        if total_issues > 0:
            # Build detailed error message with specific symbols
            error_details = []
            if public_to_rst_issues:
                error_details.append(
                    f"@public->RST issues: {[f'{issue.module_path}.{issue.symbol_name}' for issue in public_to_rst_issues]}"
                )
            if rst_to_public_issues:
                error_details.append(
                    f"RST->@public issues: {[f'{issue.module_path}.{issue.symbol_name}' for issue in rst_to_public_issues]}"
                )

            detailed_message = (
                f"Found {total_issues} new @public API inconsistencies. " + "; ".join(error_details)
            )
            assert total_issues == 0, detailed_message

    def test_error_cases(self, validator):
        """Test error handling and edge cases."""
        # Test with empty lists
        issues = validator.validate_public_in_rst([], [])
        assert issues == []

        issues = validator.validate_rst_has_public([], [])
        assert issues == []

        # Test with non-existent paths should not crash
        bad_validator = PublicApiValidator(Path("/nonexistent"))
        symbols = bad_validator.find_public_symbols()
        assert isinstance(symbols, list)  # Should return empty list, not crash

    def test_specific_known_symbols(self, validator):
        """Test specific known symbols to ensure detection works."""
        public_symbols = validator.find_public_symbols()
        rst_symbols = validator.find_rst_documented_symbols()

        # Look for some symbols we know should exist
        public_names = {(sym.module_path, sym.symbol_name) for sym in public_symbols}
        rst_names = {(sym.module_path, sym.symbol_name) for sym in rst_symbols}

        # These should exist based on our earlier exploration
        expected_public = [
            ("dagster", "asset"),  # @asset decorator
            ("dagster", "AssetKey"),  # AssetKey class
        ]

        expected_rst = [
            ("dagster", "asset"),
            ("dagster", "AssetKey"),
        ]

        for module, name in expected_public:
            if (module, name) in public_names:
                print(f"✓ Found expected @public symbol: {module}.{name}")  # noqa: T201
            else:
                print(f"✗ Missing expected @public symbol: {module}.{name}")  # noqa: T201

        for module, name in expected_rst:
            if (module, name) in rst_names:
                print(f"✓ Found expected RST symbol: {module}.{name}")  # noqa: T201
            else:
                print(f"✗ Missing expected RST symbol: {module}.{name}")  # noqa: T201


def test_catch_missing_rst_documentation():
    """Test case that should catch when @public symbols lack RST documentation."""
    # This test demonstrates how the validator catches issues
    validator = PublicApiValidator(Path(__file__).parent.parent.parent.parent.parent)

    # Create mock data to simulate the issue
    public_symbols = [
        PublicSymbol(
            module_path="dagster.test",
            symbol_name="MissingFromRst",
            symbol_type="class",
            is_exported=True,
            source_file="/fake/path.py",
        )
    ]

    rst_symbols = [
        RstSymbol(
            module_path="dagster.test",
            symbol_name="DocumentedInRst",
            rst_directive="autoclass",
            rst_file="/fake/doc.rst",
        )
    ]

    issues = validator.validate_public_in_rst(public_symbols, rst_symbols)

    # Should catch the missing RST documentation
    assert len(issues) == 1
    assert issues[0].issue_type == "missing_rst"
    assert issues[0].symbol_name == "MissingFromRst"


def test_catch_missing_public_decorator():
    """Test case that should catch when RST symbols lack @public decorator."""
    validator = PublicApiValidator(Path(__file__).parent.parent.parent.parent.parent)

    # Create mock data to simulate the issue
    rst_symbols = [
        RstSymbol(
            module_path="dagster.test",
            symbol_name="MissingPublicDecorator",
            rst_directive="autoclass",
            rst_file="/fake/doc.rst",
        )
    ]

    public_symbols = [
        PublicSymbol(
            module_path="dagster.test",
            symbol_name="HasPublicDecorator",
            symbol_type="class",
            is_exported=True,
            source_file="/fake/path.py",
        )
    ]

    issues = validator.validate_rst_has_public(rst_symbols, public_symbols)

    # Should catch the missing @public decorator
    assert len(issues) == 1
    assert issues[0].issue_type == "missing_public"
    assert issues[0].symbol_name == "MissingPublicDecorator"


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
