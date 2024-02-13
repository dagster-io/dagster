from dagster import (
    AssetMaterialization,
    AssetSpec,
    Definitions,
    OpExecutionContext,
    external_asset_from_spec,
    job,
    op,
)


@op
def an_op(context: OpExecutionContext) -> None:
    context.log_event(AssetMaterialization(asset_key="external_asset"))


@job
def a_job() -> None:
    an_op()


defs = Definitions(
    assets=[external_asset_from_spec(AssetSpec("external_asset"))], jobs=[a_job]
)
