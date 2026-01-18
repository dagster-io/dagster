from dataclasses import dataclass
from typing import Annotated

import dagster as dg


class MyApiClient:
    def __init__(self, api_key: str): ...


def resolve_api_key(
    context: dg.ResolutionContext,
    api_key: str,
) -> MyApiClient:
    return MyApiClient(api_key=api_key)


@dataclass
class MyComponent(dg.Component, dg.Resolvable):
    # Resolver specifies a function used to map input from the model
    # to a value for this field
    api_client: Annotated[
        MyApiClient,
        dg.Resolver(
            resolve_api_key,
            model_field_name="api_key",
            model_field_type=str,
        ),
    ]

    def build_defs(self, context: dg.ComponentLoadContext) -> dg.Definitions: ...
