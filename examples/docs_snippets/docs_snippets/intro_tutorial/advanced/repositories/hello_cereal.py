import csv
import os

from dagster import execute_pipeline, pipeline, solid


@solid
def hello_cereal(context):
    dataset_path = os.path.join(os.path.dirname(__file__), "cereal.csv")
    with open(dataset_path, "r") as fd:
        # Read the rows in using the standard csv library
        cereals = [row for row in csv.DictReader(fd)]

    context.log.info(
        "Found {n_cereals} cereals".format(n_cereals=len(cereals))
    )

    return cereals


@pipeline
def hello_cereal_pipeline():
    hello_cereal()


if __name__ == "__main__":
    result = execute_pipeline(hello_cereal_pipeline)
