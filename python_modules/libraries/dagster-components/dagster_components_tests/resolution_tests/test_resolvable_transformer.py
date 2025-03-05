from dataclasses import dataclass
from typing import Annotated

from dagster_components.core.schema.context import ResolutionContext
from dagster_components.core.schema.resolvable_from_schema import (
    DSLFieldResolver,
    DSLSchema,
    ResolutionSpec,
    resolve_fields,
    resolve_schema_to_resolvable,
)


def test_resolve_fields_on_transform() -> None:
    fields = resolve_fields(
        schema=ExistingBusinessObjectSchema(value="1"),
        resolution_spec=TransformToExistingBusinessObject,
        context=ResolutionContext.default(),
    )
    assert fields == {"value": 1}


def test_use_transform_to_build_business_object():
    schema = ExistingBusinessObjectSchema(value="1")
    business_object = resolve_schema_to_resolvable(
        schema,
        TransformToExistingBusinessObject,
        ResolutionContext.default(),
        ExistingBusinessObject,
    )
    assert business_object.value == 1


@dataclass
class ExistingBusinessObject:
    value: int


class ExistingBusinessObjectSchema(DSLSchema):
    value: str


# TODO remove the need for this
# @dataclass
class TransformToExistingBusinessObject(ResolutionSpec[ExistingBusinessObjectSchema]):
    value: Annotated[int, DSLFieldResolver(lambda context, val: int(val))]
