from dataclasses import dataclass
from typing import Annotated, Optional

from dagster_components import Component, Model, Resolvable, Resolver
from dagster_components.test.utils import load_direct


class MyModel(Model):
    foo: str


def test_nested_resolvable():
    class ResolvableComponent(Component, Resolvable, Model):
        thing: MyModel

        def build_defs(self, _): ...  # type: ignore

    c = load_direct(
        ResolvableComponent,
        """
thing:
  foo: hi
        """,
    )
    assert c.thing.foo

    @dataclass
    class ResolveFromComponent(Component, Resolvable):
        thing: MyModel
        num: Annotated[
            int,
            Resolver(
                lambda _, v: int(v),
                model_field_type=str,
            ),
        ]

        def build_defs(self, _): ...  # type: ignore

    c = load_direct(
        ResolveFromComponent,
        """
num: '123'
thing:
  foo: hi
        """,
    )
    assert c.thing.foo

    @dataclass
    class ResolveFromListComponent(Component, Resolvable):
        thing: Optional[list[MyModel]]
        num: Annotated[
            int,
            Resolver(
                lambda _, v: int(v),
                model_field_type=str,
            ),
        ]

        def build_defs(self, _): ...  # type: ignore

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


def test_class():
    class ResolveFromComponent(Component, Resolvable):
        def __init__(
            self,
            thing: MyModel,
            num: Annotated[int, Resolver(lambda _, v: int(v), model_field_type=str)],
        ):
            self.thing = thing
            self.num = num

        def build_defs(self, _):  # type: ignore
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
    assert c.num == 123
