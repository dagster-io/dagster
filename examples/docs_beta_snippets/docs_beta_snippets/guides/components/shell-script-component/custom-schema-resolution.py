from dataclasses import dataclass
from typing import Annotated

from dagster_components import (
    Component,
    ComponentLoadContext,
    FieldResolver,
    ResolutionContext,
    ResolvableSchema,
)

import dagster as dg


class MyApiClient:
    def __init__(self, api_key: str): ...


class MyComponentSchema(ResolvableSchema):
    api_key: str


def resolve_api_key(
    context: ResolutionContext, schema: MyComponentSchema
) -> MyApiClient:
    return MyApiClient(api_key=schema.api_key)


@dataclass
class MyComponent(Component):
    # FieldResolver specifies a function used to map input matching the schema
    # to a value for this field
    api_client: Annotated[MyApiClient, FieldResolver(resolve_api_key)]

    @classmethod
    def get_schema(cls) -> type[MyComponentSchema]:
        return MyComponentSchema

    def build_defs(self, load_context: ComponentLoadContext) -> dg.Definitions: ...
