from dagster import asset


def execute_query(query):
    del query


# start_example


@asset(group_name="cereal_assets")
def nabisco_cereals():
    execute_query(
        "CREATE TABLE nabisco_cereals AS SELECT * FROM cereals WHERE manufacturer = 'Nabisco'"
    )


# end_example
