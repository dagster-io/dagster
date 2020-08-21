import csv
import os

from dagster import execute_pipeline, pipeline, solid


@solid
def load_cereals(context):
    csv_path = os.path.join(os.path.dirname(__file__), "cereal.csv")
    with open(csv_path, "r") as fd:
        cereals = [row for row in csv.DictReader(fd)]

    context.log.info(
        "Found {n_cereals} cereals".format(n_cereals=len(cereals))
    )
    return cereals


@solid
def sort_by_calories(context, cereals):
    sorted_cereals = list(
        sorted(cereals, key=lambda cereal: cereal["calories"])
    )
    context.log.info(
        "Least caloric cereal: {least_caloric}".format(
            least_caloric=sorted_cereals[0]["name"]
        )
    )
    context.log.info(
        "Most caloric cereal: {most_caloric}".format(
            most_caloric=sorted_cereals[-1]["name"]
        )
    )


@pipeline
def serial_pipeline():
    sort_by_calories(load_cereals())


if __name__ == "__main__":
    result = execute_pipeline(serial_pipeline)
    assert result.success
