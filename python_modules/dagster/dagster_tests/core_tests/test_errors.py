import sys

from dagster._utils.error import serializable_error_info_from_exc_info


def test_syntax_error_serialized_message():
    serialized_error = None

    try:
        eval(
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


def test_from_none():
    def _raise():
        raise Exception("yaho")

    def _wrap(from_none):
        try:
            _raise()
        except:
            if from_none:
                raise Exception("wrapped") from None
            else:
                raise Exception("wrapped")

    try:
        _wrap(from_none=False)
    except:
        err = serializable_error_info_from_exc_info(sys.exc_info())

    assert err  # pyright: ignore[reportPossiblyUnboundVariable]
    assert err.context

    try:
        _wrap(from_none=True)
    except:
        err = serializable_error_info_from_exc_info(sys.exc_info())

    assert err
    assert err.context is None
