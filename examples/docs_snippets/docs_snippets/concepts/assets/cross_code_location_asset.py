# start_code_location_1

# code_location_1.py

from dagster import Definitions, asset


@asset
def code_location_1_asset():
    return 5


code_location_1 = Definitions(
    assets=[code_location_1_asset],
)

# end_code_location_1

# start_code_location_2

# code_location_2.py

from dagster import AssetKey, Definitions, SourceAsset, asset

code_location_1_source_asset = SourceAsset(key=AssetKey("code_location_1_asset"))


@asset
def code_location_2_asset(code_location_1_asset):
    return code_location_1_asset + 6


code_location_2 = Definitions(
    assets=[code_location_2_asset, code_location_1_source_asset],
)

# end_code_location_2
