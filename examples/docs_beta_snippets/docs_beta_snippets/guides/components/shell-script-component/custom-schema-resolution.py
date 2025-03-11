from dataclasses import dataclass
from typing import Annotated

from dagster_components import (
    Component,
    ComponentLoadContext,
    ResolutionContext,
    ResolvableModel,
    ResolvedFrom,
    Resolver,
)

import dagster as dg


class MyApiClient:
    def __init__(self, api_key: str): ...


class MyComponentModel(ResolvableModel):
    api_key: str


def resolve_api_key(
    context: ResolutionContext, schema: MyComponentModel
) -> MyApiClient:
    return MyApiClient(api_key=schema.api_key)


@dataclass
class MyComponent(Component, ResolvedFrom[MyComponentModel]):
    # FieldResolver specifies a function used to map input matching the schema
    # to a value for this field
    api_client: Annotated[MyApiClient, Resolver(resolve_api_key)]

    def build_defs(self, load_context: ComponentLoadContext) -> dg.Definitions: ...
