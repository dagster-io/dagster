import dagster as dg


# `processed_files` is defined in a different code location (cross_location_da_check_asset.py).
# This unconditioned check targets it but lives here, so it must be excluded from the ride-along
# set resolved for `processed_files` in the other location (repo-scoping).
@dg.asset_check(asset=dg.AssetKey("processed_files"), name="external_not_null")
def external_not_null() -> dg.AssetCheckResult:
    return dg.AssetCheckResult(passed=True)


defs = dg.Definitions(asset_checks=[external_not_null])
