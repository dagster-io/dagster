def execute_query(query):
    del query


# start_marker

from dagster import asset


@asset
def sugary_cereals() -> None:
    execute_query(
        "CREATE TABLE sugary_cereals AS SELECT * FROM cereals WHERE sugar_grams > 10"
    )


@asset(deps=[sugary_cereals])
def shopping_list() -> None:
    execute_query("CREATE TABLE shopping_list AS SELECT * FROM sugary_cereals")


# end_marker
