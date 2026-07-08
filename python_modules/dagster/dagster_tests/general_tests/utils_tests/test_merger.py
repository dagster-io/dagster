from dagster._utils.merger import merge_dicts, reverse_dict


def test_merge_dicts_combines_keys():
    assert merge_dicts({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}


def test_merge_dicts_later_values_win():
    # When a key appears in more than one input, the last one takes priority.
    assert merge_dicts({"a": 1, "b": 2}, {"a": 3}) == {"a": 3, "b": 2}


def test_merge_dicts_single_dict():
    assert merge_dicts({"a": 1}) == {"a": 1}


def test_merge_dicts_ignores_empty_dicts():
    assert merge_dicts({"a": 1}, {}, {"c": 3}) == {"a": 1, "c": 3}


def test_merge_dicts_does_not_mutate_inputs():
    first = {"a": 1}
    second = {"b": 2}
    merge_dicts(first, second)
    assert first == {"a": 1}
    assert second == {"b": 2}


def test_reverse_dict_swaps_keys_and_values():
    assert reverse_dict({"a": 1, "b": 2}) == {1: "a", 2: "b"}


def test_reverse_dict_empty():
    assert reverse_dict({}) == {}


def test_reverse_dict_duplicate_values_keep_last_key():
    # Two keys map to the same value: the last key encountered wins.
    assert reverse_dict({"a": 1, "b": 1}) == {1: "b"}
