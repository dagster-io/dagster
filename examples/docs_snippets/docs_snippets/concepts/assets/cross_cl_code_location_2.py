# start
# code_location_2.py
import json

from dagster import AssetKey, Definitions, asset


@asset(deps=["code_location_1_asset"])
def code_location_2_asset():
    with open("/data/code_location_1_asset.json") as f:
        x = json.load(f)

    with open("/data/code_location_2_asset.json", "w+") as f:
        json.dump(x + 6, f)


defs = Definitions(assets=[code_location_2_asset])

# end
