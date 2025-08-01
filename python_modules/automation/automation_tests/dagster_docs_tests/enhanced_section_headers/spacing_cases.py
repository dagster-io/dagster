"""Docstring fixtures for testing spacing and whitespace issues."""

from dagster._annotations import public


@public
class SpacingCases:
    """Fixtures for testing section header spacing issues."""

    @public
    def incorrect_spacing(self, param1):
        """Function with spacing issues in headers.

        Args :
            param1: Description (space before colon)

        Returns:
            Description of return value
        """
        pass

    @public
    def whitespace_variants(self, param1, param2, param3):
        """Function with whitespace issues.

        Args:
            param1: Tab before header

        Args:
            param2: Spaces before header

        Args:
            param3: Whitespace after colon
        """
        pass

    @public
    def block_quote_formatting_issues(self, param1, param2):
        """Function with formatting that may cause block quote issues.

        Args:
        param1: Description without proper indentation
        param2: Another line

        Some text that might break RST parsing
        """
        pass
