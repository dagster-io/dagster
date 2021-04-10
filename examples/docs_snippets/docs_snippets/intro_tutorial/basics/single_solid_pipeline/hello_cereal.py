"""isort:skip_file"""

# start_solid_marker
import csv
import pathlib

from dagster import pipeline, solid


@solid
def hello_cereal(context):
    # Assumes the dataset is in the same directory as this Python file
    dataset_path = pathlib.Path(__file__).parent / "cereal.csv"
    with open(dataset_path, "r") as fd:
        # Read the rows in using the standard csv library
        cereals = [row for row in csv.DictReader(fd)]

    context.log.info(f"Found {len(cereals)} cereals")


# end_solid_marker


# start_pipeline_marker
@pipeline
def hello_cereal_pipeline():
    hello_cereal()


# end_pipeline_marker

# start_execute_marker
from dagster import execute_pipeline

if __name__ == "__main__":
    result = execute_pipeline(hello_cereal_pipeline)

# end_execute_marker
