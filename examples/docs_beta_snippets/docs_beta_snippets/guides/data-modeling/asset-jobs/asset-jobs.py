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


# start_marker
import dagster as dg

all_assets_job = dg.define_asset_job(name="all_assets_job")
sugary_cereals_job = dg.define_asset_job(
    name="sugary_cereals_job", selection="sugary_cereals"
)


defs = dg.Definitions(
    assets=[sugary_cereals, shopping_list],
    jobs=[all_assets_job, sugary_cereals_job],
)
