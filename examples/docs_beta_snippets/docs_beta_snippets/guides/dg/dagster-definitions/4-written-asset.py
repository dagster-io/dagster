import dagster as dg


@dg.asset(group_name="my_group")
def my_asset(context: dg.AssetExecutionContext) -> None:
    """Asset that greets you."""
    context.log.info("hi!")
