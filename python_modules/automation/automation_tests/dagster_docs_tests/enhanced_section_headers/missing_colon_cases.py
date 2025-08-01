"""Docstring fixtures for testing missing colon detection."""

from dagster._annotations import public


@public
class MissingColonCases:
    """Fixtures for testing section headers missing colons."""

    @public
    def basic_missing_colons(self, param1, param2):
        """Function with missing colon in section header.

        Args:
            param1: Description of parameter
            param2: Another parameter

        Returns:
            Description of return value
        """
        pass

    @public
    def multiple_header_errors(self, param1):
        """Function with multiple header errors.

        Args:
        param1: Missing colon above

        Returns:
        Wrong capitalization above

        Examplesjdkfjdk:
        Corrupted header above
        """
        pass

    @public
    def unexpected_indentation_case(self, param1, param2):
        """Function causing unexpected indentation.

        Args:
        param1: This line will cause unexpected indentation error
            param2: Description
        """
        pass
