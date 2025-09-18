import dagster as dg


@dg.asset
def asset_with_in_app_check():
    return dg.MaterializeResult(metadata={"num_rows": dg.MetadataValue.int(7)})


@dg.asset
def asset_with_code_and_in_app_check():
    return dg.MaterializeResult(metadata={"num_rows": dg.MetadataValue.int(5)})


@dg.asset_check(asset="asset_with_code_and_in_app_check")
def code_defined_asset_check():
    return dg.AssetCheckResult(passed=True)


def get_assets_and_checks():
    return [
        asset_with_in_app_check,
        asset_with_code_and_in_app_check,
        code_defined_asset_check,
    ]
