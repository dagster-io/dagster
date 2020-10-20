import pickle

import pytest
from dagster.utils import frozendict


def test_frozendict():
    d = frozendict({"foo": "bar"})
    with pytest.raises(RuntimeError):
        d["zip"] = "zowie"


def test_pickle_frozendict():
    orig_dict = [{"foo": "bar"}]
    data = pickle.dumps(orig_dict)
    loaded_dict = pickle.loads(data)

    assert orig_dict == loaded_dict
