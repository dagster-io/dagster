import sys

from dagit.schema.errors import PythonError


def test_python_error():
    def func():
        raise Exception('bar')

    try:
        func()
    except:  # pylint: disable=W0702
        python_error = PythonError.from_sys_exc_info(sys.exc_info())

    assert python_error
    assert isinstance(python_error.message, str)
    assert isinstance(python_error.stack, list)
    assert len(python_error.stack) == 2
    assert 'bar' in python_error.stack[1]
