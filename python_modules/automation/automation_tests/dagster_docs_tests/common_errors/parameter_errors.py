"""Docstring fixtures for testing parameter description errors."""

from dagster._annotations import public


@public
class ParameterErrorFixtures:
    """Fixtures for testing parameter description error detection."""

    @public
    def missing_parameter_descriptions(self, param1, param2, param3):
        """Function with missing parameter descriptions.

        Args:
            param1:  # Missing description
            param2: Valid description
            param3:  # Another missing description

        Returns:
            Description of return value
        """
        pass

    @public
    def malformed_type_annotations(self, param1, param2, param3):
        """Function with malformed type annotations.

        Args:
            param1 (str: Missing closing parenthesis
            param2 (int)): Extra closing parenthesis
            param3 str): Missing opening parenthesis

        Returns:
            Description of return value
        """
        pass

    @public
    def inconsistent_parameter_format(self, param1, param2, param3, param4):
        """Function with inconsistent parameter formatting.

        Args:
            param1 (str): Formatted with type annotation
            param2: No type annotation
            param3 (int) - Wrong separator, should use colon
            param4 (bool): description with
                multiple lines but inconsistent formatting

        Returns:
            Description of return value
        """
        pass
