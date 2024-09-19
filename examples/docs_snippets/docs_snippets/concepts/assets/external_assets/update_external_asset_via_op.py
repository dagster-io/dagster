from dagster import (
    AssetMaterialization,
    AssetSpec,
    Definitions,
    OpExecutionContext,
    job,
    op,
)


@op
def an_op(context: OpExecutionContext) -> None:
    context.log_event(AssetMaterialization(asset_key="external_asset"))


@job
def a_job() -> None:
    an_op()


defs = Definitions(assets=[AssetSpec("external_asset")], jobs=[a_job])
