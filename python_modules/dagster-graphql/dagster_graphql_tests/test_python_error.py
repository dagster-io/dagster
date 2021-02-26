import sys

from dagster.utils.error import serializable_error_info_from_exc_info
from dagster_graphql.schema.errors import GraphenePythonError


def test_python_error():
    def func():
        raise Exception("bar")

    try:
        func()
    except:  # pylint: disable=W0702
        python_error = GraphenePythonError(serializable_error_info_from_exc_info(sys.exc_info()))

    assert python_error
    assert isinstance(python_error.message, str)
    assert isinstance(python_error.stack, list)
    assert len(python_error.stack) == 2
    assert "bar" in python_error.stack[1]
