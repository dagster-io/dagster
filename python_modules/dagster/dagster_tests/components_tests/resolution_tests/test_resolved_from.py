from collections.abc import Sequence
from dataclasses import dataclass
from typing import Annotated, Literal, Optional, Union

import pytest
from dagster.components import Component
from dagster.components.resolved.base import Model, Resolvable
from dagster.components.resolved.errors import ResolutionException
from dagster.components.resolved.model import Resolver

from dagster_tests.components_tests.utils import load_component_for_test


class MyModel(Model):
    foo: str


def test_nested_resolvable():
    class ResolvableComponent(Component, Resolvable, Model):
        thing: MyModel

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

    c = ResolveFromListComponent.resolve_from_yaml(
        """
thing:
  foo: hi
        """,
    )
    assert isinstance(c.thing, FooModel)
    assert c.thing.foo == "hi"

    c = ResolveFromListComponent.resolve_from_yaml(
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
    class ResolveFromUnionComponent(Component, Resolvable):
        thing: Union[FooModel, BarModel]

    c = load_component_for_test(
        ResolveFromUnionComponent,
        """
thing:
  type: foo
  value: hi
        """,
    )
    assert isinstance(c.thing, FooModel)
    assert c.thing.value == "hi"

    c = load_component_for_test(
        ResolveFromUnionComponent,
        """
thing:
  type: bar
  value: hello
        """,
    )
    assert isinstance(c.thing, BarModel)
    assert c.thing.value == "hello"


def test_union_nested_custom_resolver():
    class FooNonModel:
        def __init__(self, foo: str):
            self.foo = foo

    class BarNonModel:
        def __init__(self, bar: str):
            self.bar = bar

    class FooModel(Model):
        foo: str

    class BarModel(Model):
        bar: str

    # We nest complex custom resolvers in the union
    # Under the hood, this will choose the resolver whose model_field_type matches the input model type
    @dataclass
    class ResolveUnionResolversComponent(Component, Resolvable):
        thing: Union[
            Annotated[
                FooNonModel,
                Resolver(lambda _, v: FooNonModel(foo=v.foo), model_field_type=FooModel),
            ],
            Annotated[
                BarNonModel,
                Resolver(lambda _, v: BarNonModel(bar=v.bar), model_field_type=BarModel),
            ],
        ]

    c = ResolveUnionResolversComponent.resolve_from_yaml(
        """
thing:
  foo: hi
        """,
    )
    assert isinstance(c.thing, FooNonModel)
    assert c.thing.foo == "hi"

    c = ResolveUnionResolversComponent.resolve_from_yaml(
        """
thing:
  bar: hello
        """,
    )
    assert isinstance(c.thing, BarNonModel)
    assert c.thing.bar == "hello"


def _raise_exc():
    raise Exception("test")


def test_union_nested_custom_resolver_no_match():
    class FooNonModel:
        def __init__(self, foo: str):
            self.foo = foo

    class BarNonModel:
        def __init__(self, bar: str):
            self.bar = bar

    class FooModel(Model):
        foo: str

    class BarModel(Model):
        bar: str

    @dataclass
    class ResolveUnionResolversComponent(Component, Resolvable):
        thing: Union[
            Annotated[
                FooNonModel,
                Resolver(lambda _, v: _raise_exc(), model_field_type=FooModel),
            ],
            Annotated[
                BarNonModel,
                Resolver(lambda _, v: _raise_exc(), model_field_type=BarModel),
            ],
        ]

    with pytest.raises(
        ResolutionException,
        match=r"No resolver matched the field value",
    ):
        ResolveUnionResolversComponent.resolve_from_yaml(
            """
thing:
  foo: hi
        """,
        )
