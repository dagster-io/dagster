import csv
import os

from dagster import execute_pipeline, pipeline, solid


# start_complex_pipeline_marker_0
@solid
def load_cereals(_):
    dataset_path = os.path.join(os.path.dirname(__file__), "cereal.csv")
    with open(dataset_path, "r") as fd:
        cereals = [row for row in csv.DictReader(fd)]
    return cereals


@solid
def sort_by_calories(_, cereals):
    sorted_cereals = list(
        sorted(cereals, key=lambda cereal: cereal["calories"])
    )
    least_caloric = sorted_cereals[0]["name"]
    most_caloric = sorted_cereals[-1]["name"]
    return (least_caloric, most_caloric)


@solid
def sort_by_protein(_, cereals):
    sorted_cereals = list(
        sorted(cereals, key=lambda cereal: cereal["protein"])
    )
    least_protein = sorted_cereals[0]["name"]
    most_protein = sorted_cereals[-1]["name"]
    return (least_protein, most_protein)


@solid
def display_results(context, calorie_results, protein_results):
    context.log.info(
        "Least caloric cereal: {least_caloric}".format(
            least_caloric=calorie_results[0]
        )
    )
    context.log.info(
        "Most caloric cereal: {most_caloric}".format(
            most_caloric=calorie_results[-1]
        )
    )
    context.log.info(
        "Least protein-rich cereal: {least_protein}".format(
            least_protein=protein_results[0]
        )
    )
    context.log.info(
        "Most protein-rich cereal: {most_protein}".format(
            most_protein=protein_results[-1]
        )
    )


@pipeline
def complex_pipeline():
    cereals = load_cereals()
    display_results(
        calorie_results=sort_by_calories(cereals),
        protein_results=sort_by_protein(cereals),
    )


# end_complex_pipeline_marker_0

if __name__ == "__main__":
    result = execute_pipeline(complex_pipeline)
    assert result.success


def test_complex_pipeline():
    res = execute_pipeline(complex_pipeline)
    assert res.success
    assert len(res.solid_result_list) == 4
    for solid_res in res.solid_result_list:
        assert solid_res.success
