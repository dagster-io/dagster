"""Docstring fixtures for testing complex error combinations."""

from dagster._annotations import public


@public
class ComplexErrorCombinationFixtures:
    """Fixtures for testing combinations of multiple errors."""

    @public
    def multiple_error_types(self, param1, param2, param3):
        """Function with multiple errors.

        args:  # Wrong capitalization
        param1: Not indented properly
            param2 (str: Missing closing paren
        param3: `Unmatched backtick

        returns  # Missing colon
        A return value with ``unmatched double backticks

        raises::  # Double colon
            ValueError: When `something goes wrong
        """
        pass

    @public
    def nested_formatting_errors(self, param1, param2):
        """Function with nested formatting errors.

        Args:
            param1: A parameter with a `code snippet` and a
                    second line with `unmatched backtick

                    And a nested list:

                    - Item 1
                    * Mixed bullet (wrong)
                      - Nested item
                        * Double nested with wrong bullet

            param2: Another parameter with issues:

                .. code-block: python  # Missing double colon

                    # This code block is malformed
                    def example(:  # Syntax error in code
                        return "test"

        Returns:
            Complex return description with `multiple formatting issues:

            - Return item 1
            - Return item with `unmatched backtick
            - Item with bad link `click here <>`_
        """
        pass
