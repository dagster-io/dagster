import dagster as dg


def execute_query(query):
    del query


# start_marker_assets
@dg.asset
def sugary_cereals() -> None:
    execute_query(
        "CREATE TABLE sugary_cereals AS SELECT * FROM cereals WHERE sugar_grams > 10"
    )


@dg.asset(deps=[sugary_cereals])
def shopping_list() -> None:
    execute_query("CREATE TABLE shopping_list AS SELECT * FROM sugary_cereals")


# end_marker_assets


# start_marker_jobs
@dg.job
def all_assets_job():
    sugary_cereals()
    shopping_list()


@dg.job
def sugary_cereals_job():
    sugary_cereals()


# end_marker_jobs
