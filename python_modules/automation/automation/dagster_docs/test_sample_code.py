"""Sample code file for testing docstring line number reporting.

This file contains functions with docstrings that have intentional errors
to test that line numbers are reported relative to the file, not the docstring.
"""


def good_function():
    """A function with a valid docstring.

    This function has no errors and should pass validation.

    Returns:
        str: A greeting message
    """
    return "Hello, world!"


def function_with_bad_rst():
    """A function with invalid RST syntax.

    This function has invalid RST that should trigger an error.
    Here's some broken RST: `unclosed backtick

    Args:
        param: A parameter

    Returns:
        None: Nothing is returned
    """
    pass


def function_with_bad_section_header():
    """A function with malformed section headers.

    This function has incorrectly formatted section headers.

    args:
        param: This should be "Args:" not "args:"

    returns:
        This should be "Returns:" not "returns:"
    """
    pass


def function_with_multiple_errors():
    """A function with multiple docstring errors.

    This function has both bad RST and bad section headers.
    Here's some broken RST: `unclosed backtick

    args:
        param: Bad section header (should be Args:)

    returns:
        Bad section header and more `broken RST
    """
    pass
