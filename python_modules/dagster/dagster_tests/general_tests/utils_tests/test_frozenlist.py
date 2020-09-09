import pickle

from dagster.utils import frozendict


def test_pickle_frozenlist():
    orig_list = [1, "a", {}]
    data = pickle.dumps(orig_list)
    loaded_list = pickle.loads(data)

    assert orig_list == loaded_list
