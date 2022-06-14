# pylint: disable=redefined-outer-name

from dagster import asset

# start_example


@asset(group_name="cereal_assets")
def nabisco_cereals():
    return [1, 2, 3]


# end_example
