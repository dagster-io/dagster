from dataclasses import dataclass
from typing import Annotated, Optional

from dagster_components import Component
from dagster_components.resolved.model import ResolvableModel, ResolvedFrom, Resolver
from dagster_components.test.utils import load_direct


def test_nested_resolvable():
    class MyModel(ResolvableModel):
        foo: str

    class ResolvableComponent(Component, ResolvableModel):
        thing: MyModel

        def build_defs(self, _):
            return []

    c = load_direct(
        ResolvableComponent,
        """
thing:
  foo: hi
        """,
    )
    assert c.thing.foo

    class ComponentModel(ResolvableModel):
        thing: MyModel
        num: str

    @dataclass
    class ResolveFromComponent(Component, ResolvedFrom[ComponentModel]):
        thing: MyModel
        num: Annotated[int, Resolver(lambda _, v: int(v))]

        def build_defs(self, _):
            return []

    c = load_direct(
        ResolveFromComponent,
        """
num: '123'
thing:
  foo: hi
        """,
    )
    assert c.thing.foo

    class ListComponentModel(ResolvableModel):
        thing: Optional[list[MyModel]]
        num: str

    @dataclass
    class ResolveFromListComponent(Component, ResolvedFrom[ListComponentModel]):
        thing: Optional[list[MyModel]]
        num: Annotated[int, Resolver(lambda _, v: int(v))]

        def build_defs(self, _):
            return []

    c = load_direct(
        ResolveFromListComponent,
        """
num: '123'
thing:
    - foo: hi
    - foo: bye
        """,
    )
    assert c.thing
    assert c.thing[0].foo
