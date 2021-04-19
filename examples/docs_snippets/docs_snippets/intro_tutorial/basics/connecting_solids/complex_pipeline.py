import csv

import requests
from dagster import execute_pipeline, pipeline, solid


# start_complex_pipeline_marker_0
@solid
def download_cereals(_):
    response = requests.get(
        "https://raw.githubusercontent.com/dagster-io/dagster/master/examples/docs_snippets/docs_snippets/intro_tutorial/cereal.csv"
    )
    lines = response.text.split("\n")
    return [row for row in csv.DictReader(lines)]


@solid
def find_highest_calorie_cereal(_, cereals):
    sorted_cereals = list(
        sorted(cereals, key=lambda cereal: cereal["calories"])
    )
    return sorted_cereals[-1]["name"]


@solid
def find_highest_protein_cereal(_, cereals):
    sorted_cereals = list(
        sorted(cereals, key=lambda cereal: cereal["protein"])
    )
    return sorted_cereals[-1]["name"]


@solid
def display_results(context, most_calories, most_protein):
    context.log.info(f"Most caloric cereal: {most_calories}")
    context.log.info(f"Most protein-rich cereal: {most_protein}")


@pipeline
def complex_pipeline():
    cereals = download_cereals()
    display_results(
        most_calories=find_highest_calorie_cereal(cereals),
        most_protein=find_highest_protein_cereal(cereals),
    )


# end_complex_pipeline_marker_0

# start_complex_pipeline_marker_1
def test_complex_pipeline():
    res = execute_pipeline(complex_pipeline)
    assert res.success
    assert len(res.solid_result_list) == 4
    for solid_res in res.solid_result_list:
        assert solid_res.success


# end_complex_pipeline_marker_1
