# code_location_1.py
from dagster import Definitions, asset


@asset
def code_location_1_asset():
    return 5


defs = Definitions(assets=[code_location_1_asset])
