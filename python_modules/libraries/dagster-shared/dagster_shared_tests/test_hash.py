from typing import NamedTuple

import pytest
from dagster_shared.utils.hash import hash_collection


def test_hash_collection():
    # lists have different hashes depending on order
    assert hash_collection([1, 2, 3]) == hash_collection([1, 2, 3])
    assert hash_collection([1, 2, 3]) != hash_collection([2, 1, 3])

    # dicts have same hash regardless of order
    assert hash_collection({"a": 1, "b": 2}) == hash_collection({"b": 2, "a": 1})

    assert hash_collection(set(range(10))) == hash_collection(set(range(10)))

    with pytest.raises(AssertionError):
        hash_collection(object())  # pyright: ignore[reportArgumentType]

    class Foo(NamedTuple):
        a: list[int]
        b: dict[str, int]
        c: str

    with pytest.raises(Exception):
        hash(Foo([1, 2, 3], {"a": 1}, "alpha"))

    class Bar(Foo):
        def __hash__(self):
            return hash_collection(self)

    assert hash(Bar([1, 2, 3], {"a": 1}, "alpha")) == hash(Bar([1, 2, 3], {"a": 1}, "alpha"))
