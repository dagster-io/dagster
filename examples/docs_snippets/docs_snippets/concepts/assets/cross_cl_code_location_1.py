import os

os.makedirs("/tmp/data", exist_ok=True)
# start

# code_location_1.py
import json

from dagster import Definitions, asset


@asset
def code_location_1_asset():
    with open("/tmp/data/code_location_1_asset.json", "w+") as f:
        json.dump(5, f)


defs = Definitions(assets=[code_location_1_asset])

# end
