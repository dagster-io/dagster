import dagster as dg


@dg.op
def an_op(context: dg.OpExecutionContext) -> None:
    context.log_event(dg.AssetMaterialization(asset_key="external_asset"))


@dg.job
def a_job() -> None:
    an_op()


defs = dg.Definitions(assets=[dg.AssetSpec("external_asset")], jobs=[a_job])
