from dagster import (
    OpExecutionContext,
    asset,
)


@asset(config_schema={"a_string": str, "an_int": int})
def before(context: OpExecutionContext):
    assert context.op_config["a_string"] == "foo"
    assert context.op_config["an_int"] == 2


from dagster import ConfigurableResource, Definitions, EnvVar, asset
from dagster._core.execution.context.compute import OpExecutionContext
from dagster_airbyte import AirbyteResource


@asset
def an_asset(airbyte_resource: AirbyteResource):
    pass


defs = Definitions(
    assets=[an_asset],
    resources={
        "airbyte_resource": AirbyteResource(
            host="localhost", password=EnvVar("PASSWORD_ENVVAR"), port=8001, api_version="v1"
        )
    },
)


class YourResource(ConfigurableResource):
    api_key: str
    app_key: str


@asset
def migrated_asset(your_resource: YourResource):
    assert your_resource


@asset
def unmigrated_asset(context: OpExecutionContext):
    assert context.resources.your_resource


defs = Definitions(
    assets=[migrated_asset, unmigrated_asset],
    resources={"your_resource": YourResource(api_key="api_key", app_key="app_key")},
)


from dagster import Definitions, InitResourceContext, OpExecutionContext, asset, resource


class AResource:
    def __init__(self, value: str):
        self.value = value


@resource(config_schema={"value": str})
def a_resource(context: InitResourceContext):
    return AResource(context.resource_config["value"])


@asset(required_resource_keys={"a_resource"})
def an_asset(context: OpExecutionContext):
    assert context.resources.a_resource.value == "foo"


defs = Definitions(
    assets=[an_asset],
    resources={"a_resource": a_resource.configured({"value": "foo"})}
)
