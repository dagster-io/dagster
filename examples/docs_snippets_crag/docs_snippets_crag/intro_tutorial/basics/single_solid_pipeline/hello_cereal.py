"""isort:skip_file"""

# start_solid_marker
import requests
import csv
from dagster import pipeline, solid


@solid
def hello_cereal(context):
    response = requests.get("https://docs.dagster.io/assets/cereal.csv")
    lines = response.text.split("\n")
    cereals = [row for row in csv.DictReader(lines)]
    context.log.info(f"Found {len(cereals)} cereals")

    return cereals


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
