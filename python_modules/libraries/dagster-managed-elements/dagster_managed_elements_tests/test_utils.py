from dagster_managed_elements import ManagedElementDiff
from dagster_managed_elements.utils import diff_dicts


def test_diff_dicts():
    config_dict = {"foo": "bar", "nested": {"qwerty": "uiop", "new": "field"}, "same": "as"}
    dst_dict = {"baz": "qux", "nested": {"qwerty": "hjkl", "old": "field"}, "same": "as"}

    assert (diff_dicts(config_dict, dst_dict)) == (
        (
            ManagedElementDiff()
            .add("foo", "bar")
            .delete("baz", "qux")
            .with_nested(
                "nested",
                ManagedElementDiff()
                .modify("qwerty", "hjkl", "uiop")
                .add("new", "field")
                .delete("old", "field"),
            )
        )
    )

    # Ensure a bunch of adds works
    empty_dict = {}
    assert diff_dicts(config_dict, empty_dict) == (
        ManagedElementDiff()
        .add("foo", "bar")
        .add("same", "as")
        .with_nested(
            "nested",
            ManagedElementDiff().add("qwerty", "uiop").add("new", "field"),
        )
    )

    # Bunch of deletes
    empty_dict = {}
    assert diff_dicts(empty_dict, config_dict) == (
        ManagedElementDiff()
        .delete("foo", "bar")
        .delete("same", "as")
        .with_nested(
            "nested",
            ManagedElementDiff().delete("qwerty", "uiop").delete("new", "field"),
        )
    )

    # Changing a key from a non-dict to a dict should be treated as a delete and add nested
    partial_dict = {"foo": "bar", "nested": "not-a-dict", "same": "as"}
    assert diff_dicts(config_dict, partial_dict) == (
        ManagedElementDiff()
        .delete("nested", "not-a-dict")
        .with_nested(
            "nested",
            ManagedElementDiff().add("qwerty", "uiop").add("new", "field"),
        )
    )


def test_diff_dicts_custom_comparison_fn():
    config_dict = {"foo": "bar", "nested": {"qwerty": "uiop", "new": "field"}, "same": "as"}
    dst_dict = {"baz": "qux", "nested": {"qwerty": "hjkl", "old": "field"}, "same": "as"}

    # Custom comparison which ignores the "querty" key
    assert (
        diff_dicts(
            config_dict, dst_dict, custom_compare_fn=lambda k, sv, dv: k == "qwerty" or sv == dv
        )
    ) == (
        (
            ManagedElementDiff()
            .add("foo", "bar")
            .delete("baz", "qux")
            .with_nested(
                "nested",
                ManagedElementDiff().add("new", "field").delete("old", "field"),
            )
        )
    )
