from typing import Literal, Optional

import pydantic
import pytest
from dagster._check import CheckError
from dagster._core.definitions.tags import NamespacedTagSet


def test_invalid_tag_set() -> None:
    class MyJunkTagSet(NamespacedTagSet):
        junk: int

        @classmethod
        def namespace(cls) -> str:
            return "dagster"

    with pytest.raises(
        CheckError, match="Type annotation for field 'junk' is not str, Optional\\[str\\]"
    ):
        MyJunkTagSet(junk=1)


def test_basic_tag_set_validation() -> None:
    class MyValidTagSet(NamespacedTagSet):
        foo: Optional[str] = None
        bar: Optional[str] = None

        @classmethod
        def namespace(cls) -> str:
            return "dagster"

    with pytest.raises(pydantic.ValidationError):
        MyValidTagSet(foo="lorem", bar=lambda x: x)  # type: ignore

    with pytest.raises(pydantic.ValidationError):
        MyValidTagSet(foo="lorem", baz="ipsum")  # type: ignore


def test_tag_set_with_literal() -> None:
    class MyValidTagSet(NamespacedTagSet):
        foo: Optional[Literal["apple", "banana"]] = None
        bar: Optional[str] = None

        @classmethod
        def namespace(cls) -> str:
            return "dagster"

    MyValidTagSet(foo="apple")

    with pytest.raises(pydantic.ValidationError):
        MyValidTagSet(foo="lorem")  # type: ignore


def test_basic_tag_set_functionality() -> None:
    class MyValidTagSet(NamespacedTagSet):
        foo: Optional[str] = None
        bar: Optional[str] = None

        @classmethod
        def namespace(cls) -> str:
            return "dagster"

    tag_set = MyValidTagSet(foo="lorem", bar="ipsum")
    assert tag_set.foo == "lorem"
    assert tag_set.bar == "ipsum"

    assert tag_set.extract((dict(tag_set))) == tag_set
    assert tag_set.extract({}) == MyValidTagSet(foo=None, bar=None)

    assert dict(tag_set) == {"dagster/foo": "lorem", "dagster/bar": "ipsum"}
