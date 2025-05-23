from dataclasses import dataclass, field
from typing import Annotated, Literal, Optional, Union

import dagster as dg
import pytest
from dagster import Component, Model, Resolvable, ResolvedAssetSpec
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.definitions_class import Definitions
from dagster.components.resolved.core_models import AssetPostProcessor, AssetSpecKwargs
from dagster.components.resolved.errors import ResolutionException
from dagster.components.resolved.model import Resolver
from pydantic import BaseModel, ConfigDict, Field


def test_basic():
    @dataclass
    class MyThing(Resolvable):
        name: str

    MyThing.resolve_from_yaml(
        """
name: hello
        """
    )


def test_error():
    class Foo: ...

    @dataclass
    class MyNewThing(Resolvable):
        name: str
        foo: Foo

    with pytest.raises(
        ResolutionException, match=r"Could not derive resolver for annotation\W*foo:"
    ):
        MyNewThing.resolve_from_yaml("")


def test_error_core_model_suggestion():
    @dataclass
    class MyKeyThing(Resolvable):
        key: AssetKey

    with pytest.raises(
        ResolutionException,
        match=r".*An annotated resolver for AssetKey is available, you may wish to use it instead: ResolvedAssetKey",
    ):
        MyKeyThing.resolve_from_yaml("")


def test_nested():
    @dataclass
    class OtherThing(Resolvable):
        num: int

    @dataclass
    class MyThing(Resolvable):
        name: str
        other_thing: OtherThing
        other_things: Optional[list[OtherThing]]

    MyThing.resolve_from_yaml(
        """
name: hi
other_thing:
    num: 4
other_things:
    - num: 4
""",
    )


def test_custom_resolution():
    class Foo:
        def __init__(self, name):
            self.name = name

    def _resolve_foo(context, name: str):
        return Foo(name)

    @dataclass
    class MyThing(Resolvable):
        name: str
        foo: Annotated[
            Foo,
            Resolver(
                _resolve_foo,
                model_field_type=str,
                model_field_name="foo_name",
            ),
        ]
        stuff: list[str] = field(default_factory=list)

    thing = MyThing.resolve_from_yaml(
        """
name: hello
foo_name: steve
"""
    )
    assert thing.foo.name == "steve"


def test_passthru():
    @dataclass
    class MyThing(Resolvable):
        foo: Annotated[str, Resolver.passthrough()]

    thing = MyThing.resolve_from_yaml(
        """
foo: bar
"""
    )
    assert thing.foo == "bar"

    thing = MyThing.resolve_from_yaml(
        """
foo: "{{ template_var }}"
"""
    )
    assert thing.foo == "{{ template_var }}"


def test_passthru_does_not_process_nested_resolvers():
    class Foo(BaseModel):
        name: Annotated[str, Resolver(lambda context, name: name.upper())]

    @dataclass
    class MyThing(Resolvable):
        foo: Annotated[Foo, Resolver.passthrough()]

    thing = MyThing.resolve_from_yaml(
        """
foo:
  name: bar
"""
    )

    # Nested resolvers are not processed
    assert thing.foo.name == "bar"


def test_py_model():
    class Foo:
        def __init__(self, name):
            self.name = name

    def _resolve_foo(context, name: str):
        return Foo(name)

    class MyThing(Resolvable, BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)  # to allow Foo

        name: str = "bad"
        foo: Annotated[
            Foo,
            Resolver(
                _resolve_foo,
                model_field_type=str,
                model_field_name="foo_name",
            ),
        ]

    thing = MyThing.resolve_from_yaml(
        """
foo_name: steve
"""
    )
    assert thing.name == "bad"
    assert thing.foo.name == "steve"


def test_legacy_core_components_compat():
    @dataclass
    class Example(Resolvable):
        asset_specs: list[ResolvedAssetSpec]

    ex = Example.resolve_from_yaml("""
asset_specs:
    - key: foo
    - key: bar
""")

    assert ex.asset_specs[0].key == AssetKey("foo")


def test_class():
    class Person(Resolvable):
        random: str  # ensure random annotations ignored

        def __init__(
            self,
            name: str,
            age: int,
        ): ...

    Person.resolve_from_yaml(
        """
name: Rei
age: 7
""",
    )

    class Flexible(Resolvable):
        def __init__(
            self,
            *args,
            name: str,
            **kwargs,
        ): ...

    Flexible.resolve_from_yaml(
        """
name: flex
    """,
    )


def test_bad_class():
    class Empty(Resolvable): ...

    with pytest.raises(ResolutionException, match="class with __init__"):
        Empty.resolve_from_yaml("")

    class JustSelf(Resolvable):
        def __init__(
            self,
        ): ...

    JustSelf.resolve_from_yaml("")

    class PosOnly(Resolvable):
        def __init__(
            self,
            a: int,
            /,
            b: int,
        ): ...

    with pytest.raises(ResolutionException, match="positional only parameter"):
        PosOnly.resolve_from_yaml("")


def test_component_docs():
    class RangeTest(Model):
        type: Literal["range"] = Field(..., description="Must be 'range'.")
        name: str

    class SumTest(Model):
        type: Literal["sum"] = Field(..., description="Must be 'sum'")
        name: str

    class TestSuiteComponent(Component, Resolvable, Model):
        asset_key: str = Field(
            ..., description="The asset key to test. Slashes are parsed into key parts."
        )
        tests: list[Union[RangeTest, SumTest]]

        def build_defs(self, context):
            return Definitions()

    model_cls = TestSuiteComponent.get_model_cls()
    assert model_cls
    assert model_cls.model_fields["asset_key"].description
    json_schema = model_cls.model_json_schema()
    assert json_schema["$defs"]["RangeTest"]["properties"]["type"]["description"]
    assert json_schema["$defs"]["SumTest"]["properties"]["type"]["description"]


def test_nested_not_resolvable():
    @dataclass
    class Child:
        name: str

    @dataclass
    class Parent(Resolvable):
        children: list[Child]

    with pytest.raises(ResolutionException, match="Resolvable subclass"):
        Parent.resolve_from_yaml("")


def test_post_process():
    @dataclass
    class Test(Resolvable):
        post_process: AssetPostProcessor

    with pytest.raises(Exception, match="junk_extra_input"):
        Test.resolve_from_yaml(
            """
post_process:
  target: '*'
  attributes:
    junk_extra_input: hi
    """
        )


def test_desc():
    asset_model = AssetSpecKwargs.model()
    for field_name, field_info in asset_model.model_fields.items():
        assert field_info.description, f"{field_name} must have description"


def test_nested_from_model():
    def _resolve_from_obj(context, model):
        assert model.foo
        assert model.bar
        return "cool"

    @dataclass
    class Double(Resolvable):
        foo: Optional[list[Annotated[str, Resolver.from_model(_resolve_from_obj)]]]

    with pytest.raises(Exception):
        Double.model()

    @dataclass
    class Opt(Resolvable):
        foo: Optional[Annotated[str, Resolver.from_model(_resolve_from_obj)]]

    with pytest.raises(Exception):
        Opt.model()

    @dataclass
    class Lizt(Resolvable):
        foo: list[Annotated[str, Resolver.from_model(_resolve_from_obj)]]

    with pytest.raises(Exception):
        Lizt.model()

    @dataclass
    class Works(Resolvable):
        foo: Annotated[str, Resolver.from_model(_resolve_from_obj)]
        bar: str

    w = Works.resolve_from_yaml("""
foo: foo
bar: bar
""")
    assert w.foo == "cool"


def test_scope():
    class DailyPartitionDefinitionModel(Resolvable, Model):
        type: Literal["daily"] = "daily"
        start_date: str
        end_offset: int = 0

    class Example(Resolvable, Model):
        part: Annotated[
            dg.DailyPartitionsDefinition,
            Resolver.default(
                model_field_type=DailyPartitionDefinitionModel,
                can_inject=True,
            ),
        ]

        def build_defs(self, context) -> dg.Definitions:
            return dg.Definitions()

    daily = dg.DailyPartitionsDefinition(start_date="2025-01-01")
    ex = Example.resolve_from_yaml(
        """
part: "{{ daily }}"
""",
        scope={"daily": daily},
    )

    assert ex.part == daily
