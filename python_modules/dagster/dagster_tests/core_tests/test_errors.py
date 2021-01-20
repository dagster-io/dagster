import sys

from dagster.utils.error import serializable_error_info_from_exc_info


def test_syntax_error_serialized_message():
    serialized_error = None

    try:
        eval(  # pylint: disable=eval-used
            """
foo = bar
            """
        )
    except SyntaxError:
        serialized_error = serializable_error_info_from_exc_info(sys.exc_info())

    assert serialized_error

    assert (
        serialized_error.message
        == """  File "<string>", line 2
    foo = bar
        ^
SyntaxError: invalid syntax
"""
    )
