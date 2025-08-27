def execute_query(query):
    del query


# start_basic_dependencies
import dagster as dg


@dg.asset
def sugary_cereals() -> None:
    execute_query(
        "CREATE TABLE sugary_cereals AS SELECT * FROM cereals WHERE sugar_grams > 10"
    )


@dg.asset(deps=[sugary_cereals])
def shopping_list() -> None:
    execute_query("CREATE TABLE shopping_list AS SELECT * FROM sugary_cereals")


# end_basic_dependencies


# start_code_location_one_asset_decorator
import json

import dagster as dg


@dg.asset
def code_location_1_asset():
    with open("/tmp/data/code_location_1_asset.json", "w+") as f:
        json.dump(5, f)


# end_code_location_one_asset_decorator


# start_code_location_two_asset_decorator
import json

import dagster as dg


@dg.asset(deps=["code_location_1_asset"])
def code_location_2_asset():
    with open("/tmp/data/code_location_1_asset.json") as f:
        x = json.load(f)

    with open("/tmp/data/code_location_2_asset.json", "w+") as f:
        json.dump(x + 6, f)


# end_code_location_two_asset_decorator
