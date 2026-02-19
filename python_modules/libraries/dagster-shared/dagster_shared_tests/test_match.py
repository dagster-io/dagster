from collections.abc import Sequence
from typing import Any, Literal, NamedTuple, Union

import pytest
from dagster_shared.match import match_type


# Helper to simulate the is_named_tuple_instance logic used in match_type
class MyTuple(NamedTuple):
    x: int
    y: str


@pytest.mark.parametrize(
    "obj,type_,expected",
    [
        # Concrete types
        (5, int, True),
        ("hello", str, True),
        (None, type(None), True),
        (5.5, int, False),
        (5.5, Any, True),
        ("abc", Any, True),
        ([1], Any, True),
        # Union
        (5, Union[int, str], True),  # noqa: UP007
        ("hi", Union[int, str], True),  # noqa: UP007
        (5.0, Union[int, str], False),  # noqa: UP007
        # Union via pipe syntax (types.UnionType)
        (5, int | str, True),
        ("hi", int | str, True),
        (5.0, int | str, False),
        # Literal
        ("hello", Literal["hello", "world"], True),
        ("nope", Literal["hello", "world"], False),
        (3, Literal[3, 5], True),
        (4, Literal[3, 5], False),
        # list[]
        ([1, 2, 3], list[int], True),
        ([1, "x"], list[int], False),
        ([], list[int], True),
        # Sequence[] support
        ([1, 2], Sequence[int], True),
        ((1, 2), Sequence[int], True),
        ({1, 2}, Sequence[int], False),
        # tuple[...] fixed-length
        ((1, "x"), tuple[int, str], True),
        ((1, 2), tuple[int, str], False),
        ((1,), tuple[int, str], False),
        # tuple[...] variable-length
        ((1, 2, 3), tuple[int, ...], True),
        ((1, "x"), tuple[int, ...], False),
        # dict[]
        ({"a": 1, "b": 2}, dict[str, int], True),
        ({"a": 1, 2: "b"}, dict[str, int], False),
        ({}, dict[str, int], True),
        # NamedTuple
        (MyTuple(1, "a"), NamedTuple, True),
        ((1, "a"), NamedTuple, False),
        # tuple of types
        ("abc", (int, str), True),
        ("abc", (int, Literal["abc", "def"]), True),
        ("ghi", (int, Literal["abc", "def"]), False),
    ],
)
def test_match_type(obj, type_, expected):
    assert match_type(obj, type_) == expected
