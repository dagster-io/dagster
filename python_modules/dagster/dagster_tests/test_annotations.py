import sys
from typing import NamedTuple, get_type_hints

from typing_extensions import Annotated

from dagster._annotations import (
    PUBLIC,
    deprecated,
    experimental,
    is_deprecated,
    is_experimental,
    is_public,
    public,
)


def test_public_annotation():
    class Foo:
        @public
        def bar(self):
            pass

    assert is_public(Foo.bar)


def test_public_constant_for_namedtuple():
    class Foo(NamedTuple("_Foo", [("bar", Annotated[int, PUBLIC])])):
        ...

    hints = (
        get_type_hints(Foo, include_extras=True)
        if sys.version_info >= (3, 9)
        else get_type_hints(Foo)
    )
    assert hints["bar"] == Annotated[int, PUBLIC]


def test_deprecated():
    class Foo:
        @deprecated
        def bar(self):
            pass

    assert is_deprecated(Foo.bar)


def test_experimental():
    class Foo:
        @experimental
        def bar(self):
            pass

    assert is_experimental(Foo.bar)
