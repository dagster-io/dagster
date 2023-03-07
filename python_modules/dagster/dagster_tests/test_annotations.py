import sys
import warnings
from abc import abstractmethod
from typing import NamedTuple, get_type_hints

import pytest
from dagster._annotations import (
    PUBLIC,
    PublicAttr,
    deprecated,
    experimental,
    is_deprecated,
    is_experimental,
    is_public,
    public,
    quiet_experimental,
)
from typing_extensions import Annotated


@pytest.mark.parametrize(
    "decorator,predicate",
    [(public, is_public), (experimental, is_experimental), (deprecated, is_deprecated)],
)
class TestAnnotations:
    def test_annotated_method(self, decorator, predicate):
        class Foo:
            @decorator
            def bar(self):
                pass

        assert predicate(Foo, "bar")

    def test_annotated_property(self, decorator, predicate):
        class Foo:
            @decorator
            @property
            def bar(self):
                pass

        assert predicate(Foo, "bar")

    def test_annotated_staticmethod(self, decorator, predicate):
        class Foo:
            @decorator
            @staticmethod
            def bar():
                pass

        assert predicate(Foo, "bar")

    def test_annotated_classmethod(self, decorator, predicate):
        class Foo:
            @decorator
            @classmethod
            def bar(cls):
                pass

        assert predicate(Foo, "bar")

    def test_annotated_abstractmethod(self, decorator, predicate):
        class Foo:
            @decorator
            @abstractmethod
            def bar(self):
                pass

        assert predicate(Foo, "bar")


def test_public_attr():
    class Foo(NamedTuple("_Foo", [("bar", PublicAttr[int])])):
        ...

    hints = (
        get_type_hints(Foo, include_extras=True)
        if sys.version_info >= (3, 9)
        else get_type_hints(Foo)
    )
    assert hints["bar"] == Annotated[int, PUBLIC]


def test_experimental_quiet_experimental() -> None:
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        @experimental
        def my_experimental_function(my_arg) -> None:
            pass

        assert len(w) == 0
        my_experimental_function("foo")
        assert len(w) == 1

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        @experimental
        def my_experimental_function(my_arg) -> None:
            pass

        @quiet_experimental
        def my_quiet_wrapper(my_arg) -> None:
            my_experimental_function(my_arg)

        assert len(w) == 0
        my_quiet_wrapper("foo")
        assert len(w) == 0
