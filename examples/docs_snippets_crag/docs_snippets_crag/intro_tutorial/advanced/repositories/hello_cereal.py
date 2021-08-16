import csv

import requests
from dagster import execute_pipeline, pipeline, solid


@solid
def hello_cereal(context):
    response = requests.get("https://docs.dagster.io/assets/cereal.csv")
    lines = response.text.split("\n")
    cereals = [row for row in csv.DictReader(lines)]
    context.log.info(f"Found {len(cereals)} cereals")

    return cereals


@pipeline
def hello_cereal_pipeline():
    hello_cereal()


if __name__ == "__main__":
    result = execute_pipeline(hello_cereal_pipeline)
