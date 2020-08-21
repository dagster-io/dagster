from contextlib import contextmanager

import pytest


@contextmanager
def assert_no_warnings():
    # https://stackoverflow.com/questions/45671803/how-to-use-pytest-to-assert-no-warning-is-raised
    with pytest.warns(None) as record:
        yield
    assert len(record) == 0, "Unexpected warnings: {warnings}".format(
        warnings=[str(record[i]) for i in range(len(record))]
    )
