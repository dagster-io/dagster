def execute_query(query):
    del query


# start_marker

from dagster import asset


@asset
def upstream_asset():
    execute_query("CREATE TABLE sugary_cereals AS SELECT * FROM cereals")


@asset(non_argument_deps={"upstream_asset"})
def downstream_asset():
    execute_query("CREATE TABLE shopping_list AS SELECT * FROM sugary_cereals")


# end_marker
