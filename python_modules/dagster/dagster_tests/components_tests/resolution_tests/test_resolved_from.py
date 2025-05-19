from dataclasses import dataclass
from typing import Annotated, Optional

from dagster.components import Component
from dagster.components.resolved.base import Model, Resolvable
from dagster.components.resolved.model import Resolver
from dagster.components.test.build_components import build_component_for_test


class MyModel(Model):
    foo: str


def test_nested_resolvable():
    class ResolvableComponent(Component, Resolvable, Model):
        thing: MyModel

        def build_defs(self, _): ...  # type: ignore

    c = build_component_for_test(
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

    c = build_component_for_test(
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

    c = build_component_for_test(
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

    c = build_component_for_test(
        ResolveFromComponent,
        """
num: '123'
thing:
  foo: hi
        """,
    )
    assert c.thing.foo
    assert c.num == 123
