from dagster import (
    AssetSpec,
    Definitions,
    OpExecutionContext,
    AssetMaterialization,
    op,
    job,
    external_asset_from_spec,
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
