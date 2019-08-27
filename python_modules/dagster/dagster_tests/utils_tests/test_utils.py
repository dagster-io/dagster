import os

import pytest

from dagster.check import ParameterCheckError
from dagster.utils import ensure_dir, ensure_gen, ensure_single_item


def test_ensure_single_item():
    assert ensure_single_item({'foo': 'bar'}) == ('foo', 'bar')
    with pytest.raises(ParameterCheckError, match='Expected dict with single item'):
        ensure_single_item({'foo': 'bar', 'baz': 'quux'})


def test_ensure_gen():
    zero = ensure_gen(0)
    assert next(zero) == 0
    with pytest.raises(StopIteration):
        next(zero)


def test_ensure_dir(tmpdir):
    testdir = os.path.join(str(tmpdir), 'test', 'dir', 'for', 'testing', 'ensure_dir')
    assert not os.path.exists(testdir)
    ensure_dir(testdir)
    assert os.path.exists(testdir)
    assert os.path.isdir(testdir)
    ensure_dir(testdir)
