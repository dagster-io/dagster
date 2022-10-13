from dagster_managed_stacks import ManagedStackDiff
from dagster_managed_stacks.utils import diff_dicts


def test_diff_dicts():

    config_dict = {"foo": "bar", "nested": {"qwerty": "uiop", "new": "field"}, "same": "as"}
    dst_dict = {"baz": "qux", "nested": {"qwerty": "hjkl", "old": "field"}, "same": "as"}

    assert (diff_dicts(config_dict, dst_dict)) == (
        (
            ManagedStackDiff()
            .add("foo", "bar")
            .delete("baz", "qux")
            .with_nested(
                "nested",
                ManagedStackDiff()
                .modify("qwerty", "hjkl", "uiop")
                .add("new", "field")
                .delete("old", "field"),
            )
        )
    )

    # Ensure a bunch of adds works
    empty_dict = {}
    assert diff_dicts(config_dict, empty_dict) == (
        ManagedStackDiff()
        .add("foo", "bar")
        .add("same", "as")
        .with_nested(
            "nested",
            ManagedStackDiff().add("qwerty", "uiop").add("new", "field"),
        )
    )

    # Bunch of deletes
    empty_dict = {}
    assert diff_dicts(empty_dict, config_dict) == (
        ManagedStackDiff()
        .delete("foo", "bar")
        .delete("same", "as")
        .with_nested(
            "nested",
            ManagedStackDiff().delete("qwerty", "uiop").delete("new", "field"),
        )
    )

    # Changing a key from a non-dict to a dict should be treated as a delete and add nested
    partial_dict = {"foo": "bar", "nested": "not-a-dict", "same": "as"}
    assert diff_dicts(config_dict, partial_dict) == (
        ManagedStackDiff()
        .delete("nested", "not-a-dict")
        .with_nested(
            "nested",
            ManagedStackDiff().add("qwerty", "uiop").add("new", "field"),
        )
    )
