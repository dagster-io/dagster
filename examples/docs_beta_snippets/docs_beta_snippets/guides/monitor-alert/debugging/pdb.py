import dagster as dg


@dg.asset
def pdb_asset(context: dg.AssetExecutionContext):
    x = 10
    # highlight-start
    context.pdb.set_trace()
    # highlight-end
    x += 5
    x += 20
