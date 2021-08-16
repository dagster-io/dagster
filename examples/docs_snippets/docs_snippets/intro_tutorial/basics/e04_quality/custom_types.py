import csv

import requests
from dagster import DagsterType, InputDefinition, OutputDefinition, pipeline, solid


# start_custom_types_marker_0
def is_list_of_dicts(_, value):
    return isinstance(value, list) and all(isinstance(element, dict) for element in value)


SimpleDataFrame = DagsterType(
    name="SimpleDataFrame",
    type_check_fn=is_list_of_dicts,
    description="A naive representation of a data frame, e.g., as returned by csv.DictReader.",
)
# end_custom_types_marker_0


# start_custom_types_marker_1


@solid(output_defs=[OutputDefinition(SimpleDataFrame)])
def download_csv(context):
    response = requests.get("https://docs.dagster.io/assets/cereal.csv")
    lines = response.text.split("\n")
    context.log.info("Read {n_lines} lines".format(n_lines=len(lines)))
    return [row for row in csv.DictReader(lines)]


@solid(input_defs=[InputDefinition("cereals", SimpleDataFrame)])
def sort_by_calories(context, cereals):
    sorted_cereals = sorted(cereals, key=lambda cereal: cereal["calories"])
    context.log.info(f'Most caloric cereal: {sorted_cereals[-1]["name"]}')


# end_custom_types_marker_1


@pipeline
def custom_type_pipeline():
    sort_by_calories(download_csv())
