import sys

import pytest
from dagster.utils.error import serializable_error_info_from_exc_info


@pytest.mark.skipif(
    sys.version_info < (3, 6), reason="traceback exceptions not supported in python2"
)
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
