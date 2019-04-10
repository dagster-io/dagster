import pytest

from dagster.utils import frozendict


def test_frozendict():
    d = frozendict({'foo': 'bar'})
    with pytest.raises(RuntimeError):
        d['zip'] = 'zowie'
