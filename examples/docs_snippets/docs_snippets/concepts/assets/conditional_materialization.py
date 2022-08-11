import random

from dagster import Output, asset

# start_conditional


@asset(always_materialize=False)
def may_not_materialize():
    # to simulate an asset that may not always materialize.
    random.seed()
    if random.randint(1, 10) < 5:
        yield Output([1, 2, 3, 4])


@asset
def downstream(may_not_materialize):
    # will not run when may_not_materialize doesn't materialize the asset
    return may_not_materialize + [5]


# end_conditional
