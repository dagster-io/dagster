"""Docstring fixtures for testing capitalization detection."""

from dagster._annotations import public


@public
class CapitalizationCases:
    """Fixtures for testing section header capitalization."""

    @public
    def incorrect_capitalization(self, param1):
        """Function with incorrect capitalization.

        Args:
            param1: Description of parameter

        Returns:
            Description of return value

        Raises:
            ValueError: When something goes wrong
        """
        pass

    @public
    def all_caps_case(self, param1, param2):
        """Function testing case sensitivity.

        Args:
            param1: All caps version

        Args:
            param2: Mixed case version
        """
        pass

    @public
    def valid_section_headers(self, param1, param2):
        """Function with all correctly formatted headers.

        Args:
            param1: Description of parameter
            param2: Another parameter

        Returns:
            Description of return value

        Raises:
            ValueError: When something goes wrong

        Examples:
            >>> function_call()
            'result'

        Note:
            This is a note section.

        See Also:
            other_function: Related function
        """
        pass
