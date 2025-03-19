from dataclasses import dataclass
from typing import Annotated, Optional

import pytest
from dagster_components.core.component import Component
from dagster_components.resolved.errors import ResolutionException
from dagster_components.resolved.model import Resolved, Resolver
from dagster_components.test.utils import load_direct


def test_basic():
    @dataclass
    class MyThing(Component, Resolved):
        name: str

        def build_defs(self): ...

    load_direct(
        MyThing,
        """
name: hello
        """,
    )


def test_error():
    class Foo: ...

    @dataclass
    class MyNewThing(Component, Resolved):
        name: str
        foo: Foo

        def build_defs(self): ...

    with pytest.raises(ResolutionException, match="Unable to derive ResolvableModel"):
        load_direct(MyNewThing, "")


def test_nested():
    @dataclass
    class OtherThing(Resolved):
        num: int

    @dataclass
    class MyThing(Component, Resolved):
        name: str
        other_thing: Annotated[OtherThing, Resolver.from_annotation()]
        other_things: Annotated[Optional[list[OtherThing]], Resolver.from_annotation()]

        def build_defs(self): ...

    load_direct(
        MyThing,
        """
name: hi
other_thing:
    num: 4
other_things:
    - num: 4
""",
    )
