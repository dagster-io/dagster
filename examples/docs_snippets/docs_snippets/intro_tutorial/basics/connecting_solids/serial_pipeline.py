# start_serial_pipeline_marker_0
import csv
import os

from dagster import execute_pipeline, pipeline, solid


@solid
def load_cereals(context):
    csv_path = os.path.join(os.path.dirname(__file__), "cereal.csv")
    with open(csv_path, "r") as fd:
        cereals = [row for row in csv.DictReader(fd)]

    context.log.info(f"Found {len(cereals)} cereals".format())
    return cereals


@solid
def sort_by_calories(context, cereals):
    sorted_cereals = list(
        sorted(cereals, key=lambda cereal: cereal["calories"])
    )

    context.log.info(f'Most caloric cereal: {sorted_cereals[-1]["name"]}')


@pipeline
def serial_pipeline():
    sort_by_calories(load_cereals())


# end_serial_pipeline_marker_0
if __name__ == "__main__":
    result = execute_pipeline(serial_pipeline)
    assert result.success
