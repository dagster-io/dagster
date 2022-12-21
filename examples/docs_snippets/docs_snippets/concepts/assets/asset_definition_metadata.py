from dagster import asset

# start_example


@asset(metadata={"owner": "alice@mycompany.com", "priority": "high"})
def my_asset():
    return 5


# end_example
