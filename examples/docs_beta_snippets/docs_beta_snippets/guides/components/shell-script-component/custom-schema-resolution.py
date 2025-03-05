from dataclasses import dataclass
from typing import Annotated

from dagster_components import (
    Component,
    ComponentLoadContext,
    ResolvableFromSchema,
    YamlFieldResolver,
    YamlSchema,
)

import dagster as dg


class MyApiClient:
    def __init__(self, api_key: str): ...


class MyComponentSchema(YamlSchema):
    api_key: str


@dataclass
class MyComponent(Component, ResolvableFromSchema[MyComponentSchema]):
    # FieldResolver specifies a function used to map input matching the schema
    # to a value for this field
    api_client: Annotated[
        MyApiClient, YamlFieldResolver(lambda context, api_key: MyApiClient(api_key))
    ]

    def build_defs(self, load_context: ComponentLoadContext) -> dg.Definitions: ...
