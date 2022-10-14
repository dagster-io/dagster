import re

from dagster_managed_stacks import ManagedStackDiff
from dagster_managed_stacks.utils import diff_dicts


def test_diff_equality():

    assert ManagedStackDiff() == ManagedStackDiff()

    # Ensure equality ignores order
    assert (
        ManagedStackDiff()
        .add("foo", "bar")
        .delete("baz", "qux")
        .with_nested(
            "nested", ManagedStackDiff().modify("qwerty", "hjkl", "uiop").add("new", "field")
        )
    ) == (
        ManagedStackDiff()
        .with_nested(
            "nested", ManagedStackDiff().add("new", "field").modify("qwerty", "hjkl", "uiop")
        )
        .delete("baz", "qux")
        .add("foo", "bar")
    )


def test_diff_join():

    assert ManagedStackDiff().add("foo", "bar").add("baz", "qux") == ManagedStackDiff().add(
        "foo", "bar"
    ).join(ManagedStackDiff().add("baz", "qux"))

    assert (
        ManagedStackDiff()
        .add("foo", "bar")
        .delete("baz", "qux")
        .with_nested("nested", ManagedStackDiff().add("new", "field"))
        .with_nested("nested2", ManagedStackDiff().add("asdf", "asdf"))
    ) == (
        ManagedStackDiff()
        .add("foo", "bar")
        .with_nested("nested", ManagedStackDiff().add("new", "field"))
        .join(
            ManagedStackDiff()
            .delete("baz", "qux")
            .with_nested("nested2", ManagedStackDiff().add("asdf", "asdf"))
        )
    )


ANSI_ESCAPE = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")


def clean_escape(diff: ManagedStackDiff):
    return ANSI_ESCAPE.sub("", str(diff)).strip("\n")


def test_diff_string():

    assert clean_escape(ManagedStackDiff()) == ""

    assert clean_escape(ManagedStackDiff().add("foo", "bar")) == "+ foo: bar"

    assert clean_escape(ManagedStackDiff().delete("foo", "bar")) == "- foo: bar"

    assert clean_escape(ManagedStackDiff().modify("foo", "bar", "baz")) == "~ foo: bar -> baz"

    assert (
        clean_escape(
            ManagedStackDiff()
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
                ManagedStackDiff()
                .add("foo", "bar")
                .delete("baz", "qux")
                .with_nested("nested", ManagedStackDiff().add("qwerty", "uiop").add("asdf", "zxcv"))
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
                ManagedStackDiff()
                .add("foo", "bar")
                .delete("baz", "qux")
                .with_nested(
                    "nested", ManagedStackDiff().delete("qwerty", "uiop").delete("asdf", "zxcv")
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
                ManagedStackDiff()
                .add("foo", "bar")
                .delete("baz", "qux")
                .with_nested(
                    "nested", ManagedStackDiff().add("qwerty", "uiop").delete("asdf", "zxcv")
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
