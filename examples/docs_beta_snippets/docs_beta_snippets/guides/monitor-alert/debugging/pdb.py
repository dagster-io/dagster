import dagster as dg


@dg.asset
def pdb_asset(context: dg.AssetExecutionContext):
    x = 10
    context.pdb.set_trace()
    x += 5
    x += 20
