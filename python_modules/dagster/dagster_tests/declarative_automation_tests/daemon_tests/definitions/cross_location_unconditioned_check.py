import dagster as dg


# `processed_files` is defined in a different code location
@dg.asset_check(asset=dg.AssetKey("processed_files"))
def external_non_null() -> dg.AssetCheckResult:
    return dg.AssetCheckResult(passed=True)


defs = dg.Definitions(asset_checks=[external_non_null])
