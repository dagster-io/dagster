from dataclasses import dataclass
from typing import Optional

import pytest
from dagster_components.core.component import Component
from dagster_components.resolved.errors import ResolutionException
from dagster_components.resolved.model import Resolved
from dagster_components.test.utils import load_direct


class BlankComponent(Component):
    def build_defs(self): ...  # type: ignore


def test_basic():
    @dataclass
    class MyThing(BlankComponent, Resolved):
        name: str

    load_direct(
        MyThing,
        """
name: hello
        """,
    )


def test_error():
    class Foo: ...

    @dataclass
    class MyNewThing(BlankComponent, Resolved):
        name: str
        foo: Foo

        def build_defs(self): ...

    with pytest.raises(ResolutionException, match="Could not derive resolver for annotation foo:"):
        load_direct(MyNewThing, "")


def test_nested():
    @dataclass
    class OtherThing(Resolved):
        num: int

    @dataclass
    class MyThing(BlankComponent, Resolved):
        name: str
        other_thing: OtherThing
        other_things: Optional[list[OtherThing]]

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


def test_class():
    class Person(BlankComponent, Resolved):
        random: str  # ensure random annotations ignored

        def __init__(
            self,
            name: str,
            age: int,
        ): ...

        def build_defs(self): ...

    load_direct(
        Person,
        """
name: Rei
age: 7
""",
    )

    class Flexible(BlankComponent, Resolved):
        def __init__(
            self,
            *args,
            name: str,
            **kwargs,
        ): ...

    load_direct(
        Flexible,
        """
name: flex
    """,
    )


def test_bad_class():
    class Empty(BlankComponent, Resolved): ...

    with pytest.raises(ResolutionException, match="class with non empty __init__"):
        load_direct(Empty, "")

    class JustSelf(BlankComponent, Resolved):
        def __init__(
            self,
        ): ...

    with pytest.raises(ResolutionException, match="class with non empty __init__"):
        load_direct(JustSelf, "")

    class PosOnly(BlankComponent, Resolved):
        def __init__(
            self,
            a: int,
            /,
            b: int,
        ): ...

    with pytest.raises(ResolutionException, match="positional only parameter"):
        load_direct(PosOnly, "")
