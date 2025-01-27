def execute_query(query):
    del query


# start_marker

import dagster as dg


@dg.asset
def sugary_cereals() -> None:
    execute_query(
        "CREATE TABLE sugary_cereals AS SELECT * FROM cereals WHERE sugar_grams > 10"
    )


@dg.asset(deps=[sugary_cereals])
def shopping_list() -> None:
    execute_query("CREATE TABLE shopping_list AS SELECT * FROM sugary_cereals")


import json

import dagster as dg


@dg.asset
def code_location_1_asset():
    with open("/data/code_location_1_asset.json", "w+") as f:
        json.dump(5, f)


defs = dg.Definitions(assets=[code_location_1_asset])

import json

import dagster as dg


@dg.asset(deps=["code_location_1_asset"])
def code_location_2_asset():
    with open("/data/code_location_1_asset.json") as f:
        x = json.load(f)

    with open("/data/code_location_2_asset.json", "w+") as f:
        json.dump(x + 6, f)


defs = dg.Definitions(assets=[code_location_2_asset])
