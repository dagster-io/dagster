"""isort:skip_file"""

# start_pipeline_marker

from dagster import pipeline, solid


@solid
def get_name():
    return "dagster"


@solid
def hello(context, name: str):
    context.log.info(f"Hello, {name}!")


@pipeline
def hello_pipeline():
    hello(get_name())


# end_pipeline_marker


# start_execute_marker
from dagster import execute_pipeline

if __name__ == "__main__":
    result = execute_pipeline(hello_pipeline)

# end_execute_marker
