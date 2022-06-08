from dagster import asset

# start_example


@asset(metadata={"cereal_name": "Sugar Sprinkles"})
def cereal_asset():
    return 5


# end_example
