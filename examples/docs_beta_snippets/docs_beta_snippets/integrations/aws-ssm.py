from dagster_aws.ssm import ParameterStoreResource, ParameterStoreTag

import dagster as dg


@dg.asset
def example_parameter_store_asset(parameter_store: ParameterStoreResource):
    parameter_value = parameter_store.fetch_parameters(
        parameters=["my-parameter-name"]
    ).get("my-parameter-name")
    return parameter_value


@dg.asset
def example_parameter_store_asset_with_env(parameter_store: ParameterStoreResource):
    import os

    with parameter_store.parameters_in_environment():
        return os.getenv("my-other-parameter-name")


defs = dg.Definitions(
    assets=[example_parameter_store_asset, example_parameter_store_asset_with_env],
    resources={
        "parameter_store": ParameterStoreResource(
            region_name="us-west-1",
            parameter_tags=[
                ParameterStoreTag(key="my-tag-key", values=["my-tag-value"])
            ],
            with_decryption=True,
        )
    },
)
