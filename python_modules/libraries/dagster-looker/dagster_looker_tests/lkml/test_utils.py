from dagster_looker.lkml.asset_utils import deep_merge_objs


def test_deep_merge_objs_scalar() -> None:
    onto_obj = "a"
    from_obj = "b"
    assert deep_merge_objs(onto_obj, from_obj) == from_obj

    # We allow overwriting a scalar with None
    # Here, ... is our sentinel value for no change
    onto_obj = "a"
    from_obj = None
    assert deep_merge_objs(onto_obj, from_obj) == from_obj

    onto_obj = "a"
    from_obj = ...
    assert deep_merge_objs(onto_obj, from_obj) == onto_obj

    onto_obj = None
    from_obj = None
    assert deep_merge_objs(onto_obj, from_obj) is None


def test_deep_merge_objs_dict() -> None:
    onto_obj = {"a": 1, "b": 2}
    from_obj = {"b": 3, "c": 4}
    assert deep_merge_objs(onto_obj, from_obj) == {"a": 1, "b": 3, "c": 4}

    onto_obj = {"a": 1, "b": 2}
    from_obj = None
    assert deep_merge_objs(onto_obj, from_obj) == onto_obj

    onto_obj = None
    from_obj = {"b": 3, "c": 4}
    assert deep_merge_objs(onto_obj, from_obj) == from_obj

    onto_obj = {"a": {"b": 1}}
    from_obj = {"a": {"b": 2}}
    assert deep_merge_objs(onto_obj, from_obj) == from_obj


def test_deep_merge_objs_list() -> None:
    onto_obj = [1, 2]
    from_obj = [3, 4]

    assert deep_merge_objs(onto_obj, from_obj) == [1, 2, 3, 4]

    onto_obj = [{"a": 1}, {"b": 2}]
    from_obj = [{"b": 3}, {"c": 4}]
    assert deep_merge_objs(onto_obj, from_obj) == [{"a": 1}, {"b": 2}, {"b": 3}, {"c": 4}]

    onto_obj = [{"name": "a", "value": 1}, {"name": "b", "value": 2}]
    from_obj = [{"name": "b", "value": 3}, {"name": "c", "value": 4}]
    assert deep_merge_objs(onto_obj, from_obj) == [
        {"name": "a", "value": 1},
        {"name": "b", "value": 3},
        {"name": "c", "value": 4},
    ]


def test_deep_merge_objs_complex() -> None:
    onto_obj = {
        "a": 1,
        "b": 2,
        "c": {"d": 3, "e": 4},
        "f": [{"name": "a", "value": 1}, {"name": "b", "value": 2}],
    }
    from_obj = {
        "b": 3,
        "c": {"d": 4, "f": 5},
        "f": [{"name": "b", "value": 3}, {"name": "c", "value": 4}],
    }

    assert deep_merge_objs(onto_obj, from_obj) == {
        "a": 1,
        "b": 3,
        "c": {"d": 4, "e": 4, "f": 5},
        "f": [{"name": "a", "value": 1}, {"name": "b", "value": 3}, {"name": "c", "value": 4}],
    }
