import warnings
from contextlib import contextmanager


@contextmanager
def assert_no_warnings():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        yield
