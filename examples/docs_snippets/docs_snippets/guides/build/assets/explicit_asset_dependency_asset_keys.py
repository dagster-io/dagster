from dagster import AssetIn, asset


# If the upstream key has a single segment, you can specify it with a string:
@asset(ins={"upstream": AssetIn(key="upstream_asset")})
def downstream_asset(upstream):
    return upstream + [4]


# If it has multiple segments, you can provide a list:
@asset(ins={"upstream": AssetIn(key=["some_db_schema", "upstream_asset"])})
def another_downstream_asset(upstream):
    return upstream + [10]
