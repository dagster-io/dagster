from dataclasses import dataclass
from typing import Annotated

from dagster._core.definitions.definitions_class import Definitions
from dagster_components import Component, ComponentLoadContext
from dagster_components.core.schema.context import ResolutionContext
from dagster_components.core.schema.resolvable_from_schema import (
    DSLFieldResolver,
    DSLSchema,
    ResolutionSpec,
    ResolvableFromSchema,
    resolve_fields,
    resolve_schema_using_spec,
)
from typing_extensions import TypeAlias


# Not allow to modified this. Example is AssetSpec
@dataclass
class ExistingBusinessObject:
    value: int


class ExistingBusinessObjectSchema(DSLSchema):
    value: str


class ExistingBusinessObjectResolutionSpec(ResolutionSpec[ExistingBusinessObjectSchema]):
    value: Annotated[int, DSLFieldResolver(lambda context, val: int(val))]


def test_resolve_fields_on_transform() -> None:
    fields = resolve_fields(
        schema=ExistingBusinessObjectSchema(value="1"),
        resolution_spec=ExistingBusinessObjectResolutionSpec,
        context=ResolutionContext.default(),
    )
    assert fields == {"value": 1}


def test_use_transform_to_build_business_object():
    schema = ExistingBusinessObjectSchema(value="1")
    business_object = resolve_schema_using_spec(
        schema=schema,
        resolution_spec=ExistingBusinessObjectResolutionSpec,
        context=ResolutionContext.default(),
        target_type=ExistingBusinessObject,
    )
    assert business_object.value == 1


def test_with_resolution_spec_on_component():
    class ComponentWithExistingBusinessObjectSchema(DSLSchema):
        business_object: ExistingBusinessObjectSchema

    @dataclass
    class ComponentWithExistingBusinessObject(
        Component, ResolvableFromSchema[ComponentWithExistingBusinessObjectSchema]
    ):
        business_object: Annotated[
            ExistingBusinessObject,
            DSLFieldResolver.from_spec(
                ExistingBusinessObjectResolutionSpec, ExistingBusinessObject
            ),
        ]

        def build_defs(self, load_context: ComponentLoadContext) -> Definitions: ...

    comp_instance = ComponentWithExistingBusinessObject.load(
        attributes=ExistingBusinessObjectSchema(value="1"), context=ComponentLoadContext.for_test()
    )

    assert isinstance(comp_instance, ComponentWithExistingBusinessObject)
    assert comp_instance.business_object.value == 1


ExistingBusinessObjectField: TypeAlias = Annotated[
    ExistingBusinessObject,
    DSLFieldResolver.from_spec(ExistingBusinessObjectResolutionSpec, ExistingBusinessObject),
]


def test_reuse_across_components():
    class ComponentWithExistingBusinessObjectSchemaOne(DSLSchema):
        business_object: ExistingBusinessObjectSchema

    @dataclass
    class ComponentWithExistingBusinessObjectOne(
        Component, ResolvableFromSchema[ComponentWithExistingBusinessObjectSchemaOne]
    ):
        business_object: ExistingBusinessObjectField

        def build_defs(self, load_context: ComponentLoadContext) -> Definitions: ...

    class ComponentWithExistingBusinessObjectSchemaTwo(DSLSchema):
        business_object: ExistingBusinessObjectSchema

    @dataclass
    class ComponentWithExistingBusinessObjectTwo(
        Component, ResolvableFromSchema[ComponentWithExistingBusinessObjectSchemaTwo]
    ):
        business_object: ExistingBusinessObjectField

        def build_defs(self, load_context: ComponentLoadContext) -> Definitions: ...

    comp_instance_one = ComponentWithExistingBusinessObjectOne.load(
        attributes=ExistingBusinessObjectSchema(value="1"), context=ComponentLoadContext.for_test()
    )

    assert isinstance(comp_instance_one, ComponentWithExistingBusinessObjectOne)
    assert comp_instance_one.business_object.value == 1

    comp_instance_one = ComponentWithExistingBusinessObjectTwo.load(
        attributes=ExistingBusinessObjectSchema(value="2"), context=ComponentLoadContext.for_test()
    )

    assert isinstance(comp_instance_one, ComponentWithExistingBusinessObjectTwo)
    assert comp_instance_one.business_object.value == 2
