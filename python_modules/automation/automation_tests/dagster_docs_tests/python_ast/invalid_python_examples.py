"""Docstring fixtures with invalid Python code blocks."""

from dagster._annotations import public


@public
class InvalidPythonFixtures:
    """Fixtures for testing invalid Python syntax detection."""

    @public
    def python_with_syntax_error(self):
        """Example with Python syntax error.

        Examples:
            Invalid Python - syntax error:

            .. code-block:: python

                def broken_function(:  # Missing parameter name
                    return "This won't parse"

                result = broken_function()
        """
        pass

    @public
    def python_with_indentation_error(self):
        """Example with Python indentation error.

        Examples:
            Invalid Python - indentation error:

            .. code-block:: python

                def process_data(items):
                    if items:
                        for item in items:
                    print(item)  # Wrong indentation level
                        return len(items)
        """
        pass

    @public
    def python_with_unmatched_parentheses(self):
        """Example with Python unmatched parentheses.

        Examples:
            Invalid Python - unmatched parentheses:

            .. code-block:: python

                def calculate(a, b):
                    result = (a + b * 2
                    return result  # Missing closing parenthesis
        """
        pass

    @public
    def python_with_invalid_assignment(self):
        """Example with invalid Python assignment.

        Examples:
            Invalid Python - invalid assignment:

            .. code-block:: python

                def example():
                    # Invalid assignment target
                    (x + y) = 10
                    return x, y
        """
        pass

    @public
    def python_with_incomplete_structure(self):
        """Example with incomplete Python structure.

        Examples:
            Invalid Python - incomplete structure:

            .. code-block:: python

                class DataProcessor:
                    def __init__(self, config):
                        self.config = config

                    def process(self, data):
                        if data:
                            # Missing implementation

                    # Missing method completion
        """
        pass
