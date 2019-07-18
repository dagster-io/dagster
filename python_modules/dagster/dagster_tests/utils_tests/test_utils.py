import pytest

from dagster.check import ParameterCheckError
from dagster.utils import ensure_gen, ensure_single_item


def test_ensure_single_item():
    assert ensure_single_item({'foo': 'bar'}) == ('foo', 'bar')
    with pytest.raises(ParameterCheckError, match='Expected dict with single item'):
        ensure_single_item({'foo': 'bar', 'baz': 'quux'})


def test_ensure_gen():
    zero = ensure_gen(0)
    assert next(zero) == 0
    with pytest.raises(StopIteration):
        next(zero)
