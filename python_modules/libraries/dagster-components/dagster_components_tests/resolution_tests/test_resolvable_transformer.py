from collections.abc import Sequence
from dataclasses import dataclass
from typing import Annotated

from dagster._core.definitions.asset_dep import AssetDep
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition,
)
from dagster._core.definitions.definitions_class import Definitions
from dagster_components import Component, ComponentLoadContext
from dagster_components.core.schema.context import ResolutionContext
from dagster_components.core.schema.objects import AssetSpecResolutionSpec, AssetSpecSchema
from dagster_components.core.schema.resolvable_from_schema import (
    FieldResolver,
    ResolvableModel,
    ResolvedFrom,
    ResolvedKwargs,
    resolve_fields,
    resolve_schema_using_spec,
)
from dagster_components.utils import AssetKey
from typing_extensions import TypeAlias


# Not allow to modified this. Example is AssetSpec
@dataclass
class ExistingBusinessObject:
    value: int


class ExistingBusinessObjectModel(ResolvableModel):
    value: str


class ExistingBusinessObjectKwargs(ResolvedKwargs[ExistingBusinessObjectModel]):
    value: Annotated[int, FieldResolver(lambda context, val: int(val))]


def test_resolve_fields_on_transform() -> None:
    fields = resolve_fields(
        schema=ExistingBusinessObjectModel(value="1"),
        resolution_spec=ExistingBusinessObjectKwargs,
        context=ResolutionContext.default(),
    )
    assert fields == {"value": 1}


def test_use_transform_to_build_business_object():
    schema = ExistingBusinessObjectModel(value="1")
    business_object = resolve_schema_using_spec(
        schema=schema,
        resolution_spec=ExistingBusinessObjectKwargs,
        context=ResolutionContext.default(),
        target_type=ExistingBusinessObject,
    )
    assert business_object.value == 1


def test_with_resolution_spec_on_component():
    class ComponentWithExistingBusinessObjectModel(ResolvableModel):
        business_object: ExistingBusinessObjectModel

    @dataclass
    class ComponentWithExistingBusinessObject(
        Component, ResolvedFrom[ComponentWithExistingBusinessObjectModel]
    ):
        business_object: Annotated[
            ExistingBusinessObject,
            FieldResolver.from_spec(ExistingBusinessObjectKwargs, ExistingBusinessObject),
        ]

        def build_defs(self, load_context: ComponentLoadContext) -> Definitions: ...

    comp_instance = ComponentWithExistingBusinessObject.load(
        attributes=ExistingBusinessObjectModel(value="1"), context=ComponentLoadContext.for_test()
    )

    assert isinstance(comp_instance, ComponentWithExistingBusinessObject)
    assert comp_instance.business_object.value == 1


ExistingBusinessObjectField: TypeAlias = Annotated[
    ExistingBusinessObject,
    FieldResolver.from_spec(ExistingBusinessObjectKwargs, ExistingBusinessObject),
]


def test_reuse_across_components():
    class ComponentWithExistingBusinessObjectSchemaOne(ResolvableModel):
        business_object: ExistingBusinessObjectModel

    @dataclass
    class ComponentWithExistingBusinessObjectOne(
        Component, ResolvedFrom[ComponentWithExistingBusinessObjectSchemaOne]
    ):
        business_object: ExistingBusinessObjectField

        def build_defs(self, load_context: ComponentLoadContext) -> Definitions: ...

    class ComponentWithExistingBusinessObjectSchemaTwo(ResolvableModel):
        business_object: ExistingBusinessObjectModel

    @dataclass
    class ComponentWithExistingBusinessObjectTwo(
        Component, ResolvedFrom[ComponentWithExistingBusinessObjectSchemaTwo]
    ):
        business_object: ExistingBusinessObjectField

        def build_defs(self, load_context: ComponentLoadContext) -> Definitions: ...

    comp_instance_one = ComponentWithExistingBusinessObjectOne.load(
        attributes=ExistingBusinessObjectModel(value="1"), context=ComponentLoadContext.for_test()
    )

    assert isinstance(comp_instance_one, ComponentWithExistingBusinessObjectOne)
    assert comp_instance_one.business_object.value == 1

    comp_instance_one = ComponentWithExistingBusinessObjectTwo.load(
        attributes=ExistingBusinessObjectModel(value="2"), context=ComponentLoadContext.for_test()
    )

    assert isinstance(comp_instance_one, ComponentWithExistingBusinessObjectTwo)
    assert comp_instance_one.business_object.value == 2


def test_asset_spec():
    asset_schema = AssetSpecSchema(
        key="asset_key",
    )

    asset_spec = resolve_schema_using_spec(
        schema=asset_schema,
        resolution_spec=AssetSpecResolutionSpec,
        context=ResolutionContext.default(),
        target_type=AssetSpec,
    )

    assert asset_spec.key == AssetKey("asset_key")

    kitchen_sink = AssetSpecSchema(
        key="kitchen_sink",
        deps=["upstream"],
        description="A kitchen sink",
        metadata={"key": "value"},
        group_name="group_name",
        skippable=False,
        code_version="code_version",
        owners=["owner@owner.com"],
        tags={"tag": "value"},
        kinds=["kind"],
        automation_condition="{{automation_condition.eager()}}",
    )

    kitchen_sink_spec = resolve_schema_using_spec(
        schema=kitchen_sink,
        resolution_spec=AssetSpecResolutionSpec,
        context=ResolutionContext.default(),
        target_type=AssetSpec,
    )

    assert kitchen_sink_spec.key == AssetKey("kitchen_sink")
    assert kitchen_sink_spec.deps == [AssetDep(asset="upstream")]
    assert kitchen_sink_spec.description == "A kitchen sink"
    assert kitchen_sink_spec.metadata == {"key": "value"}
    assert kitchen_sink_spec.group_name == "group_name"
    assert kitchen_sink_spec.skippable is False
    assert kitchen_sink_spec.code_version == "code_version"
    assert kitchen_sink_spec.owners == ["owner@owner.com"]
    assert kitchen_sink_spec.tags == {"tag": "value", "dagster/kind/kind": ""}
    assert kitchen_sink_spec.kinds == {"kind"}
    assert isinstance(kitchen_sink_spec.automation_condition, AutomationCondition)
    assert kitchen_sink_spec.automation_condition.get_label() == "eager"


def test_asset_spec_seq() -> None:
    class SomeObjectModel(ResolvableModel):
        specs: Sequence[AssetSpecSchema]

    @dataclass
    class SomeObject(ResolvedFrom[SomeObjectModel]):
        specs: Annotated[
            Sequence[AssetSpec],
            FieldResolver(AssetSpecResolutionSpec.resolver_fn(AssetSpec).from_seq),
        ]

    some_object = resolve_schema_using_spec(
        schema=SomeObjectModel(
            specs=[
                AssetSpecSchema(key="asset1"),
                AssetSpecSchema(key="asset2"),
            ]
        ),
        resolution_spec=SomeObject,
        context=ResolutionContext.default(),
        target_type=SomeObject,
    )

    assert some_object.specs == [AssetSpec(key="asset1"), AssetSpec(key="asset2")]
