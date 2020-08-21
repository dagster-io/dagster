import pytest
from lakehouse.asset import canonicalize_path

from dagster.check import CheckError


@pytest.mark.parametrize(
    "path, expected",
    [
        ("a", ("a",)),
        ("ab", ("ab",)),
        (("a",), ("a",)),
        (("ab", "cd"), ("ab", "cd")),
        (["a"], ("a",)),
        (["ab", "cd"], ("ab", "cd")),
    ],
)
def test_canonicalize_path(path, expected):
    assert canonicalize_path(path) == expected


@pytest.mark.parametrize("path", [(1,), (1,), ((1,),), (("a", 1),), (["a", 1],)])
def test_unacceptable_paths(path):
    with pytest.raises(CheckError):
        canonicalize_path(path)
