from collections.abc import Sequence
from dataclasses import dataclass
from typing import Annotated, Literal, Optional, Union

import dagster as dg
import pytest
from dagster.components.core.context import ComponentLoadContext
from dagster.components.resolved.errors import ResolutionException

from dagster_tests.components_tests.utils import load_component_for_test


class MyModel(dg.Model):
    foo: str


def test_nested_resolvable():
    class ResolvableComponent(dg.Component, dg.Resolvable, dg.Model):
        thing: MyModel

        def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
            return dg.Definitions()

    c = load_component_for_test(
        ResolvableComponent,
        """
thing:
  foo: hi
        """,
    )
    assert c.thing.foo

    @dataclass
    class ResolveFromComponent(dg.Component, dg.Resolvable):
        thing: MyModel
        num: Annotated[
            int,
            dg.Resolver(
                lambda _, v: int(v),
                model_field_type=str,
            ),
        ]

        def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
            return dg.Definitions()

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
    class ResolveFromListComponent(dg.Component, dg.Resolvable):
        thing: Optional[list[MyModel]]
        num: Annotated[
            int,
            dg.Resolver(
                lambda _, v: int(v),
                model_field_type=str,
            ),
        ]

        def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
            return dg.Definitions()

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
    class ResolveFromComponent(dg.Component, dg.Resolvable):
        def __init__(
            self,
            thing: MyModel,
            num: Annotated[int, dg.Resolver(lambda _, v: int(v), model_field_type=str)],
        ):
            self.thing = thing
            self.num = num

        def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
            return dg.Definitions()

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
    class FooModel(dg.Model):
        foo: str

    class BarModel(dg.Model):
        bar: str

    @dataclass
    class ResolveFromListComponent(dg.Component, dg.Resolvable):
        thing: Union[FooModel, BarModel]

        def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
            return dg.Definitions()

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
    class FooModel(dg.Model):
        foo: str

    # Test a nested model, in a sequence, with a custom resolver
    class NumModel(dg.Model, dg.Resolvable):
        num: Annotated[int, dg.Resolver(lambda _, v: int(v), model_field_type=str)]

    @dataclass
    class ResolveFromListComponent(dg.Component, dg.Resolvable):
        thing: Union[FooModel, Sequence[NumModel]]

        def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
            return dg.Definitions()

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
    assert isinstance(c.thing, Sequence)
    assert len(c.thing) == 2
    assert c.thing[0].num == 123
    assert c.thing[1].num == 456


def test_union_resolvable_discriminator():
    class FooModel(dg.Model):
        type: Literal["foo"] = "foo"
        value: str

    class BarModel(dg.Model):
        type: Literal["bar"] = "bar"
        value: str

    @dataclass
    class ResolveFromUnionComponent(dg.Component, dg.Resolvable):
        thing: Union[FooModel, BarModel]

        def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
            return dg.Definitions()

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

    class FooModel(dg.Model):
        foo: str

    class BarModel(dg.Model):
        bar: str

    # We nest complex custom resolvers in the union
    # Under the hood, this will choose the resolver whose model_field_type matches the input model type
    @dataclass
    class ResolveUnionResolversComponent(dg.Component, dg.Resolvable):
        thing: Union[
            Annotated[
                FooNonModel,
                dg.Resolver(lambda _, v: FooNonModel(foo=v.foo), model_field_type=FooModel),
            ],
            Annotated[
                BarNonModel,
                dg.Resolver(lambda _, v: BarNonModel(bar=v.bar), model_field_type=BarModel),
            ],
        ]

        def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
            return dg.Definitions()

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

    class FooModel(dg.Model):
        foo: str

    class BarModel(dg.Model):
        bar: str

    @dataclass
    class ResolveUnionResolversComponent(dg.Component, dg.Resolvable):
        thing: Union[
            Annotated[
                FooNonModel,
                dg.Resolver(lambda _, v: _raise_exc(), model_field_type=FooModel),
            ],
            Annotated[
                BarNonModel,
                dg.Resolver(lambda _, v: _raise_exc(), model_field_type=BarModel),
            ],
        ]

        def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
            return dg.Definitions()

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
