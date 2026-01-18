import dagster as dg


@dg.asset(key=dg.AssetKey.from_user_string("RAW_DATA/users"))
def users(context: dg.AssetExecutionContext) -> dg.MaterializeResult: ...
