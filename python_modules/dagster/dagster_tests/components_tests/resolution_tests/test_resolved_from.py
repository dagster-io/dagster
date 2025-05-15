from collections.abc import Sequence
from dataclasses import dataclass
from typing import Annotated, Literal, Optional, Union

from dagster.components import Component
from dagster.components.resolved.base import Model, Resolvable
from dagster.components.resolved.model import Resolver

from dagster_tests.components_tests.utils import load_component_for_test


class MyModel(Model):
    foo: str


def test_nested_resolvable():
    class ResolvableComponent(Component, Resolvable, Model):
        thing: MyModel

        def build_defs(self, _): ...

    c = load_component_for_test(
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

        def build_defs(self, _): ...

    c = load_component_for_test(
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

        def build_defs(self, _): ...

    c = load_component_for_test(
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

        def build_defs(self, _):
            return []

    c = load_component_for_test(
        ResolveFromComponent,
        """
num: '123'
thing:
  foo: hi
        """,
    )
    assert c.thing.foo
    assert c.num == 123


def test_union_resolvable():
    class FooModel(Model):
        foo: str

    class BarModel(Model):
        bar: str

    @dataclass
    class ResolveFromListComponent(Component, Resolvable):
        thing: Union[FooModel, BarModel]

        def build_defs(self, _): ...

    c = load_component_for_test(
        ResolveFromListComponent,
        """
thing:
  foo: hi
        """,
    )
    assert isinstance(c.thing, FooModel)
    assert c.thing.foo == "hi"

    c = load_component_for_test(
        ResolveFromListComponent,
        """
thing:
  bar: hello
        """,
    )
    assert isinstance(c.thing, BarModel)
    assert c.thing.bar == "hello"


def test_union_resolvable_complex():
    class FooModel(Model):
        foo: str

    # Test a nested model, in a sequence, with a custom resolver
    class NumModel(Model):
        num: Annotated[int, Resolver(lambda _, v: int(v), model_field_type=str)]

    @dataclass
    class ResolveFromListComponent(Component, Resolvable):
        thing: Union[FooModel, Sequence[NumModel]]

        def build_defs(self, _): ...

    c = load_component_for_test(
        ResolveFromListComponent,
        """
thing:
  foo: hi
        """,
    )
    assert isinstance(c.thing, FooModel)
    assert c.thing.foo == "hi"

    c = load_component_for_test(
        ResolveFromListComponent,
        """
thing:
  - num: '123'
  - num: '456'
        """,
    )
    assert isinstance(c.thing, list)
    assert len(c.thing) == 2
    assert c.thing[0].num == 123
    assert c.thing[1].num == 456


def test_union_resolvable_discriminator():
    class FooModel(Model):
        type: Literal["foo"] = "foo"
        value: str

    class BarModel(Model):
        type: Literal["bar"] = "bar"
        value: str

    @dataclass
    class ResolveFromListComponent(Component, Resolvable):
        thing: Union[FooModel, BarModel]

        def build_defs(self, _): ...

    c = load_component_for_test(
        ResolveFromListComponent,
        """
thing:
  type: foo
  value: hi
        """,
    )
    assert isinstance(c.thing, FooModel)
    assert c.thing.value == "hi"

    c = load_component_for_test(
        ResolveFromListComponent,
        """
thing:
  type: bar
  value: hello
        """,
    )
    assert isinstance(c.thing, BarModel)
    assert c.thing.value == "hello"
