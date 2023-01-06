import re

from dagster_managed_elements import ManagedElementDiff


def test_diff_equality():
    assert ManagedElementDiff() == ManagedElementDiff()

    # Ensure equality ignores order
    assert (
        ManagedElementDiff()
        .add("foo", "bar")
        .delete("baz", "qux")
        .with_nested(
            "nested", ManagedElementDiff().modify("qwerty", "hjkl", "uiop").add("new", "field")
        )
    ) == (
        ManagedElementDiff()
        .with_nested(
            "nested", ManagedElementDiff().add("new", "field").modify("qwerty", "hjkl", "uiop")
        )
        .delete("baz", "qux")
        .add("foo", "bar")
    )


def test_diff_join():
    assert ManagedElementDiff().add("foo", "bar").add("baz", "qux") == ManagedElementDiff().add(
        "foo", "bar"
    ).join(ManagedElementDiff().add("baz", "qux"))

    assert (
        ManagedElementDiff()
        .add("foo", "bar")
        .delete("baz", "qux")
        .with_nested("nested", ManagedElementDiff().add("new", "field"))
        .with_nested("nested2", ManagedElementDiff().add("asdf", "asdf"))
    ) == (
        ManagedElementDiff()
        .add("foo", "bar")
        .with_nested("nested", ManagedElementDiff().add("new", "field"))
        .join(
            ManagedElementDiff()
            .delete("baz", "qux")
            .with_nested("nested2", ManagedElementDiff().add("asdf", "asdf"))
        )
    )


ANSI_ESCAPE = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")


def clean_escape(diff: ManagedElementDiff):
    return ANSI_ESCAPE.sub("", str(diff)).strip("\n")


def test_diff_string():
    assert clean_escape(ManagedElementDiff()) == ""

    assert clean_escape(ManagedElementDiff().add("foo", "bar")) == "+ foo: bar"

    assert clean_escape(ManagedElementDiff().delete("foo", "bar")) == "- foo: bar"

    assert clean_escape(ManagedElementDiff().modify("foo", "bar", "baz")) == "~ foo: bar -> baz"

    assert (
        clean_escape(
            ManagedElementDiff()
            .add("foo", "bar")
            .delete("baz", "qux")
            .modify("qwerty", "hjkl", "uiop")
        )
        == """\
+ foo: bar
- baz: qux
~ qwerty: hjkl -> uiop"""
    )

    # Only additions in a nested diff should be printed as an addition
    assert (
        (
            clean_escape(
                ManagedElementDiff()
                .add("foo", "bar")
                .delete("baz", "qux")
                .with_nested(
                    "nested", ManagedElementDiff().add("qwerty", "uiop").add("asdf", "zxcv")
                )
            )
        )
        == """\
+ foo: bar
+ nested:
  + qwerty: uiop
  + asdf: zxcv
- baz: qux"""
    )

    # Only deletions in a nested diff should be printed as a deletion
    assert (
        (
            clean_escape(
                ManagedElementDiff()
                .add("foo", "bar")
                .delete("baz", "qux")
                .with_nested(
                    "nested", ManagedElementDiff().delete("qwerty", "uiop").delete("asdf", "zxcv")
                )
            )
        )
        == """\
+ foo: bar
- baz: qux
- nested:
  - qwerty: uiop
  - asdf: zxcv"""
    )

    # Both additions and deletions in a nested diff should be printed as a modification
    assert (
        (
            clean_escape(
                ManagedElementDiff()
                .add("foo", "bar")
                .delete("baz", "qux")
                .with_nested(
                    "nested", ManagedElementDiff().add("qwerty", "uiop").delete("asdf", "zxcv")
                )
            )
        )
        == """\
+ foo: bar
- baz: qux
~ nested:
  + qwerty: uiop
  - asdf: zxcv"""
    )
