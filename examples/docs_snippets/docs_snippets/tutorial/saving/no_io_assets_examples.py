from dagster import asset


def get_snowflake_connection():
    pass


@asset
def orders():
    pass


# start_snowflake_example


@asset(deps=[orders])
def returns():
    conn = get_snowflake_connection()
    conn.execute(
        "CREATE TABLE returns AS SELECT * from orders WHERE status = 'RETURNED'"
    )


# end_snowflake_example
