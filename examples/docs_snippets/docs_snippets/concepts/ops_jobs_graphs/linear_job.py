# pylint: disable=unused-argument

# start_marker
from dagster import job, op


@op
def return_one(context) -> int:
    return 1


@op
def add_one(context, number: int) -> int:
    return number + 1


@job
def linear():
    add_one(add_one(add_one(return_one())))


# end_marker
