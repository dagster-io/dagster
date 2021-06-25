"""isort:skip_file"""

# start_pipeline_marker

from dagster import pipeline, solid


@solid
def return_one():
    return 1


@solid
def add_two(i: int):
    return i + 2


@solid
def multi_three(i: int):
    return i * 3


@pipeline
def my_pipeline():
    multi_three(add_two(return_one()))


# end_pipeline_marker

# start_execute_marker
from dagster import execute_pipeline

if __name__ == "__main__":
    result = execute_pipeline(my_pipeline)

# end_execute_marker


def execute_subset():
    # start_solid_selection_marker
    execute_pipeline(my_pipeline, solid_selection=["*add_two"])
    # end_solid_selection_marker
