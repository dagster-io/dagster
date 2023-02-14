from dagster import asset


@asset
def a_number():
    return 1
