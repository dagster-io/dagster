import os
import sys

from dagster import AssetExecutionContext, Config, Definitions, asset
from dagster._core.external_execution.subprocess import (
    SubprocessExecutionResource,
)
from dagster_external.protocol import ExternalExecutionIOMode
from pydantic import Field

# Add package container to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def get_common_extras(context: AssetExecutionContext):
    instance_storage = context.instance.storage_directory()
    storage_root = os.path.join(instance_storage, "number_example")
    if not os.path.exists(storage_root):
        os.mkdir(storage_root)
    return {"storage_root": storage_root}


def command_for_asset(key: str):
    return ["python", "-m", f"numbers_example.{key}"]


def get_env():
    return {"PYTHONPATH": os.path.dirname(os.path.abspath(__file__))}


class NumberConfig(Config):
    multiplier: int = Field(default=1)


@asset
def number_x(
    context: AssetExecutionContext, ext: SubprocessExecutionResource, config: NumberConfig
) -> None:
    extras = {**get_common_extras(context), "multiplier": config.multiplier}
    ext.run(command_for_asset("number_x"), context=context, extras=extras)


@asset
def number_y(
    context: AssetExecutionContext, ext: SubprocessExecutionResource, config: NumberConfig
):
    ext.run(
        command_for_asset("number_y"),
        context=context,
        extras=get_common_extras(context),
        env={"NUMBER_Y": "4"},
    )


@asset(deps=[number_x, number_y])
def number_sum(context: AssetExecutionContext, ext: SubprocessExecutionResource) -> None:
    ext.run(command_for_asset("number_sum"), context=context, extras=get_common_extras(context))


ext = SubprocessExecutionResource(
    input_mode=ExternalExecutionIOMode.stdio,
    output_mode=ExternalExecutionIOMode.stdio,
    env=get_env(),
)

defs = Definitions(assets=[number_x, number_y, number_sum], resources={"ext": ext})

if __name__ == "__main__":
    from dagster import instance_for_test, materialize

    with instance_for_test() as instance:
        materialize(
            [number_x, number_y, number_sum],
            instance=instance,
            resources={"ext": ext},
        )
