"""Docstring fixtures for testing indentation errors."""

from dagster._annotations import public


@public
class IndentationErrorFixtures:
    """Fixtures for testing indentation error detection."""

    @public
    def incorrect_parameter_indentation(self, param1, param2):
        """Function with incorrect parameter indentation.

        Args:
        param1: Description not indented  # Should be indented
        param2: Another description not indented  # Should be indented

        Returns:
            Correct indentation here
        """
        pass

    @public
    def mixed_indentation_levels(self, param1, param2, param3):
        """Function with mixed indentation levels.

        Args:
            param1: First parameter with correct indentation
        param2: Second parameter with incorrect indentation
                param3: Third parameter with too much indentation

        Returns:
            Description of return value
        """
        pass

    @public
    def section_content_not_indented(self, param1, param2):
        """Function with section content not indented.

        Args:
        param1: This should be indented under Args
        param2: This should also be indented

        Returns:
        The return description should be indented
        """
        pass
