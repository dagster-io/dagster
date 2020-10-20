import pickle

import pytest
from dagster.utils import frozenlist


def test_pickle_frozenlist():
    orig_list = frozenlist([1, "a", {}])
    data = pickle.dumps(orig_list)
    loaded_list = pickle.loads(data)

    assert orig_list == loaded_list


def test_hash_frozen_list():
    assert hash(frozenlist([]))
    assert hash(frozenlist(["foo", "bar"]))

    with pytest.raises(TypeError, match="unhashable type"):
        hash(frozenlist([[]]))

    with pytest.raises(TypeError, match="unhashable type"):
        hash(frozenlist([{}]))
