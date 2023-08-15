# start_w_context
from dagster import AssetExecutionContext, asset


@asset
def context_asset(context: AssetExecutionContext):
    context.log.info(f"My run ID is {context.run_id}")
    ...


# end_w_context
