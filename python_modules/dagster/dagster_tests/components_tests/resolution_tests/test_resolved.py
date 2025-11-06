from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Annotated, Any, Literal, NamedTuple, Optional, TypeAlias, Union

import dagster as dg
import pytest
from dagster.components.resolved.core_models import AssetPostProcessor, AssetSpecKwargs
from dagster.components.resolved.errors import ResolutionException
from dagster.components.resolved.model import Resolver
from dagster_shared.record import record
from pydantic import BaseModel, ConfigDict, Field, ValidationError


def test_basic():
    @dataclass
    class MyThing(dg.Resolvable):
        name: str

    MyThing.resolve_from_yaml(
        """
name: hello
        """
    )


def test_error():
    class Foo: ...

    @dataclass
    class MyNewThing(dg.Resolvable):
        name: str
        foo: Foo

    with pytest.raises(
        ResolutionException, match=r"Could not derive resolver for annotation\W*foo:"
    ):
        MyNewThing.resolve_from_yaml("")


def test_error_core_model_suggestion():
    @dataclass
    class MyKeyThing(dg.Resolvable):
        key: dg.AssetKey

    with pytest.raises(
        ResolutionException,
        match=r".*An annotated resolver for AssetKey is available, you may wish to use it instead: ResolvedAssetKey",
    ):
        MyKeyThing.resolve_from_yaml("")


def test_nested():
    @dataclass
    class OtherThing(dg.Resolvable):
        num: int

    @dataclass
    class MyThing(dg.Resolvable):
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
    class MyThing(dg.Resolvable):
        name: str
        foo: Annotated[
            Foo,
            dg.Resolver(
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
    class MyThing(dg.Resolvable):
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
    class Foo(BaseModel, dg.Resolvable):
        name: Annotated[str, dg.Resolver(lambda context, name: name.upper())]

    @dataclass
    class MyThing(dg.Resolvable):
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

    class MyThing(dg.Resolvable, BaseModel):
        model_config = ConfigDict(arbitrary_types_allowed=True)  # to allow Foo

        name: str = "bad"
        foo: Annotated[
            Foo,
            dg.Resolver(
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
    class Example(dg.Resolvable):
        asset_specs: list[dg.ResolvedAssetSpec]

    ex = Example.resolve_from_yaml("""
asset_specs:
    - key: foo
    - key: bar
""")

    assert ex.asset_specs[0].key == dg.AssetKey("foo")


def test_class():
    class Person(dg.Resolvable):
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

    class Flexible(dg.Resolvable):
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
    class Empty(dg.Resolvable): ...

    with pytest.raises(ResolutionException, match="class with __init__"):
        Empty.resolve_from_yaml("")

    class JustSelf(dg.Resolvable):
        def __init__(
            self,
        ): ...

    JustSelf.resolve_from_yaml("")

    class PosOnly(dg.Resolvable):
        def __init__(
            self,
            a: int,
            /,
            b: int,
        ): ...

    with pytest.raises(ResolutionException, match="positional only parameter"):
        PosOnly.resolve_from_yaml("")


def test_component_docs():
    class RangeTest(dg.Model):
        type: Literal["range"] = Field(..., description="Must be 'range'.")
        name: str

    class SumTest(dg.Model):
        type: Literal["sum"] = Field(..., description="Must be 'sum'")
        name: str

    class TestSuiteComponent(dg.Component, dg.Resolvable, dg.Model):
        asset_key: str = Field(
            ..., description="The asset key to test. Slashes are parsed into key parts."
        )
        tests: list[Union[RangeTest, SumTest]]

        def build_defs(self, context):
            return dg.Definitions()

    model_cls = TestSuiteComponent.get_model_cls()
    assert model_cls
    assert model_cls.model_fields["asset_key"].description
    json_schema = model_cls.model_json_schema()
    assert json_schema["$defs"]["RangeTest"]["properties"]["type"]["description"]
    assert json_schema["$defs"]["SumTest"]["properties"]["type"]["description"]

    json_schema = model_cls.model_json_schema()
    assert json_schema["$defs"]["RangeTest"]["properties"]["type"]["description"]
    assert json_schema["$defs"]["SumTest"]["properties"]["type"]["description"]


def test_nested_not_resolvable():
    @dataclass
    class Child:
        name: str

    @dataclass
    class Parent(dg.Resolvable):
        children: list[Child]

    with pytest.raises(ResolutionException, match="Resolvable subclass"):
        Parent.resolve_from_yaml("")


def test_post_process():
    @dataclass
    class Test(dg.Resolvable):
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
    class Double(dg.Resolvable):
        foo: Optional[list[Annotated[str, Resolver.from_model(_resolve_from_obj)]]]

    with pytest.raises(Exception):
        Double.model()

    @dataclass
    class Opt(dg.Resolvable):
        foo: Optional[Annotated[str, Resolver.from_model(_resolve_from_obj)]]

    with pytest.raises(Exception):
        Opt.model()

    @dataclass
    class Lizt(dg.Resolvable):
        foo: list[Annotated[str, Resolver.from_model(_resolve_from_obj)]]

    with pytest.raises(Exception):
        Lizt.model()

    @dataclass
    class Works(dg.Resolvable):
        foo: Annotated[str, Resolver.from_model(_resolve_from_obj)]
        bar: str

    w = Works.resolve_from_yaml("""
foo: foo
bar: bar
""")
    assert w.foo == "cool"


def test_default_factory():
    # Test for default_factory in dataclass
    @dataclass
    class MyThing(dg.Resolvable):
        items: dict = field(default_factory=dict)

    # empty yaml should produce an instance with the default dict
    t = MyThing.resolve_from_yaml("")
    assert isinstance(t.items, dict)
    assert t.items == {}

    # explicit yaml should override the default
    t2 = MyThing.resolve_from_yaml(
        """
items:
  a: 1
"""
    )
    assert t2.items == {"a": 1}

    # Test for default_factory in pydantic model
    class DefaultFactoryDictTestComponent(dg.Component, dg.Model, dg.Resolvable):
        config: dict[str, Any] = Field(default_factory=dict)

        def build_defs(self, context):
            return dg.Definitions()

    model_cls = DefaultFactoryDictTestComponent.get_model_cls()
    assert model_cls
    instance = DefaultFactoryDictTestComponent.resolve_from_yaml("")
    assert instance.config == {}

    class DefaultFactoryListTestComponent(dg.Component, dg.Model, dg.Resolvable):
        config: list[str] = Field(default_factory=list)

        def build_defs(self, context):
            return dg.Definitions()

    model_cls = DefaultFactoryListTestComponent.get_model_cls()
    assert model_cls
    instance = DefaultFactoryListTestComponent.resolve_from_yaml("")
    assert instance.config == []

    class DefaultFactoryTupleTestComponent(dg.Component, dg.Model, dg.Resolvable):
        config: tuple[str, ...] = Field(default_factory=tuple)

        def build_defs(self, context):
            return dg.Definitions()

    model_cls = DefaultFactoryTupleTestComponent.get_model_cls()
    assert model_cls
    instance = DefaultFactoryTupleTestComponent.resolve_from_yaml("")
    assert instance.config == ()

    class DefaultFacotoryIntTestComponent(dg.Component, dg.Model, dg.Resolvable):
        config: int = Field(default_factory=lambda: 42)

        def build_defs(self, context):
            return dg.Definitions()

    model_cls = DefaultFacotoryIntTestComponent.get_model_cls()
    assert model_cls
    instance = DefaultFacotoryIntTestComponent.resolve_from_yaml("")
    assert instance.config == 42

    class DefaultFactoryFloatTestComponent(dg.Component, dg.Model, dg.Resolvable):
        config: float = Field(default_factory=lambda: 3.14)

        def build_defs(self, context):
            return dg.Definitions()

    model_cls = DefaultFactoryFloatTestComponent.get_model_cls()
    assert model_cls
    instance = DefaultFactoryFloatTestComponent.resolve_from_yaml("")
    assert instance.config == 3.14

    class DefaultFactoryBoolTestComponent(dg.Component, dg.Model, dg.Resolvable):
        config: bool = Field(default_factory=lambda: True)

        def build_defs(self, context):
            return dg.Definitions()

    model_cls = DefaultFactoryBoolTestComponent.get_model_cls()
    assert model_cls
    instance = DefaultFactoryBoolTestComponent.resolve_from_yaml("")
    assert instance.config is True

    class DefaultFactoryStringTestComponent(dg.Component, dg.Model, dg.Resolvable):
        config: str = Field(default_factory=lambda: "default")

        def build_defs(self, context):
            return dg.Definitions()

    model_cls = DefaultFactoryStringTestComponent.get_model_cls()
    assert model_cls
    instance = DefaultFactoryStringTestComponent.resolve_from_yaml("")
    assert instance.config == "default"

    class DefaultFactoryAnyTestComponent(dg.Component, dg.Model, dg.Resolvable):
        config: Any = Field(default_factory=lambda: {"key": "value"})

        def build_defs(self, context):
            return dg.Definitions()

    model_cls = DefaultFactoryAnyTestComponent.get_model_cls()
    assert model_cls
    instance = DefaultFactoryAnyTestComponent.resolve_from_yaml("")
    assert instance.config == {"key": "value"}


def test_scope():
    class DailyPartitionDefinitionModel(dg.Resolvable, dg.Model):
        type: Literal["daily"] = "daily"
        start_date: str
        end_offset: int = 0

    class Example(dg.Resolvable, dg.Model):
        part: Annotated[
            dg.DailyPartitionsDefinition,
            Resolver.default(
                model_field_type=DailyPartitionDefinitionModel,
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


def test_inject():
    class Target(dg.Resolvable, dg.Model):
        spec: dg.ResolvedAssetSpec
        specs: list[dg.ResolvedAssetSpec]
        maybe_specs: Optional[list[dg.ResolvedAssetSpec]] = None

    boop = dg.AssetSpec("boop")
    scope = {"boop": boop, "blank": None}

    t = Target.resolve_from_yaml(
        """
spec: "{{ boop }}"
specs: "{{ [boop] }}"
maybe_specs: "{{ [boop] }}"
    """,
        scope=scope,
    )
    assert t
    assert t.spec == boop
    assert t.specs == [boop]
    assert t.maybe_specs == [boop]

    t = Target.resolve_from_yaml(
        """
spec: "{{ boop }}"
specs: "{{ [boop] }}"
maybe_specs: "{{ blank }}"
    """,
        scope=scope,
    )
    assert t
    assert t.spec == boop
    assert t.specs == [boop]
    assert t.maybe_specs is None

    t = Target.resolve_from_yaml(
        """
spec: "{{ boop }}"
specs: "{{ [boop] }}"
    """,
        scope=scope,
    )
    assert t
    assert t.spec == boop
    assert t.specs == [boop]
    assert t.maybe_specs is None


def test_inner_inject():
    class Target(dg.Resolvable, dg.Model):
        specs: list[dg.ResolvedAssetSpec]

    boop = dg.AssetSpec("boop")
    scope = {"boop": boop, "blank": None}

    with pytest.raises(ValidationError):
        Target.resolve_from_yaml(
            """
specs:
  - "{{ boop }}"
  - key: barf
    """,
            scope=scope,
        )


def test_dict():
    class Target(dg.Resolvable, dg.Model):
        thing: dict
        stuff: list

    obj = Target.resolve_from_yaml("""
thing:
    a: a
    2: 2
stuff:
    - a
    - 2
    - wow: wah
""")
    assert obj.thing == {"a": "a", 2: 2}
    assert obj.stuff == ["a", 2, {"wow": "wah"}]


def test_empty_str():
    class Thing(dg.Resolvable, dg.Model):
        name: str

    t = Thing.resolve_from_dict({"name": ""})
    assert t.name == ""


def test_plain_named_tuple():
    # plain namedtuple is not one of the types that Resolved can handle
    # so ensure errors are thrown when used

    class MyNamedTuple(NamedTuple("_", [("foo", str)])): ...

    class MyModel(dg.Resolvable, dg.Model):
        nt: MyNamedTuple

    # directly
    with pytest.raises(
        ResolutionException, match="Could not derive resolver for annotation\n  nt:"
    ):
        MyModel.model()

    class Wrapper(dg.Model):
        nt: MyNamedTuple

    class OuterWrapper(dg.Model):
        wrapper: Wrapper

    class Outer(dg.Resolvable, dg.Model):
        thing: OuterWrapper

    # or indirectly
    with pytest.raises(ResolutionException, match="Wrapper includes incompatible field\n  nt:"):
        Outer.model()


def test_resolvable_named_tuple():
    # Resolvable supports @record and dataclass, but not plain namedtuple so this is invalid.
    # We won't catch this til its used either

    class MyNamedTuple(NamedTuple("_", [("foo", str)]), dg.Resolvable): ...

    class MyModel(dg.Resolvable, dg.Model):
        nt: MyNamedTuple

    # directly
    with pytest.raises(ResolutionException, match="Invalid Resolvable type"):
        MyModel.model()

    class Wrapper(dg.Model):
        nt: MyNamedTuple

    class OuterWrapper(dg.Model):
        wrapper: Wrapper

    class Outer(dg.Resolvable, dg.Model):
        thing: OuterWrapper

    # or indirectly
    with pytest.raises(ResolutionException, match="Invalid Resolvable type"):
        Outer.model()


@record
class Foo:
    name: str


ResolvedFoo: TypeAlias = Annotated[Foo, dg.Resolver(lambda _, v: Foo(name=v), model_field_type=str)]


def test_containers():
    class Target(dg.Resolvable, dg.Model):
        li: list[ResolvedFoo]
        t: tuple[ResolvedFoo, ...]
        s: Sequence[ResolvedFoo]
        mli: Optional[list[ResolvedFoo]]
        uli: Union[list[ResolvedFoo], str]

    t = Target.resolve_from_yaml("""
li:
  - a
  - b
t:
  - c
  - d
s:
  - e
  - f
mli:
  - g
  - h
uli:
  - g
  - h
    """)

    # ensure we don't end up with a container type mismatch from resolution
    assert isinstance(t.li, list)
    assert isinstance(t.t, tuple)
    assert isinstance(t.s, Sequence)
    # or nested resolution
    assert isinstance(t.mli, list)
    assert isinstance(t.uli, list)


def test_non_resolvable_resolver():
    class Plain(dg.Model):
        num: Annotated[int, Field(description="cool")]

    class Target(dg.Model, dg.Resolvable):
        plain: Plain

    # ensure annotations on plain models are fine
    assert Target.model()

    class Mistake(dg.Model):
        num: Annotated[int, dg.Resolver(lambda _, v: v + 2)]

    class Bad(dg.Model, dg.Resolvable):
        mistake: Mistake

    # but if Resolver is used on a class that does not subclass Resolvable, we throw
    with pytest.raises(ResolutionException, match="Subclass Resolvable"):
        Bad.model()


def test_enums():
    class Thing(Enum):
        FOO = "FOO"
        BAR = "BAR"

    class Direct(dg.Resolvable, dg.Model):
        thing: Thing

    assert Direct.resolve_from_dict({"thing": "FOO"})

    class Wrapper(dg.Model):
        thing: Thing

    class Indirect(dg.Resolvable, dg.Model):
        wrapper: Wrapper

    assert Indirect.resolve_from_dict({"wrapper": {"thing": "BAR"}})


def test_dicts():
    class Inner(dg.Resolvable, dg.Model):
        name: str
        value: Optional[dg.ResolvedAssetSpec]

    class HasDict(dg.Resolvable, dg.Model):
        thing: dict[str, Inner]
        other_thing: dict[str, Inner]

    assert HasDict.resolve_from_dict(
        {
            "thing": {"a": {"name": "a", "value": {"key": "a"}}},
            "other_thing": {"b": {"name": "b", "value": {"key": "b"}}},
        }
    ) == HasDict(
        thing={"a": Inner(name="a", value=dg.AssetSpec("a"))},
        other_thing={"b": Inner(name="b", value=dg.AssetSpec("b"))},
    )

    class BadHasDict(dg.Resolvable, dg.Model):
        thing: dict[int, Inner]

    with pytest.raises(ResolutionException, match="dict key type must be str"):
        BadHasDict.resolve_from_dict({"thing": {"a": {"name": "a", "value": {"key": "a"}}}})
