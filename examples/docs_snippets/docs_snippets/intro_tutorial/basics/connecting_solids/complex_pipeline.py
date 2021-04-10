import csv
import pathlib

from dagster import execute_pipeline, pipeline, solid


# start_complex_pipeline_marker_0
@solid
def load_cereals(_):
    dataset_path = pathlib.Path(__file__).parent / "cereal.csv"
    with open(dataset_path, "r") as fd:
        cereals = [row for row in csv.DictReader(fd)]
    return cereals


@solid
def sort_by_calories(_, cereals):
    sorted_cereals = list(
        sorted(cereals, key=lambda cereal: cereal["calories"])
    )
    most_calories = sorted_cereals[-1]["name"]
    return most_calories


@solid
def sort_by_protein(_, cereals):
    sorted_cereals = list(
        sorted(cereals, key=lambda cereal: cereal["protein"])
    )
    most_protein = sorted_cereals[-1]["name"]
    return most_protein


@solid
def display_results(context, most_calories, most_protein):
    context.log.info(f"Most caloric cereal: {most_calories}")
    context.log.info(f"Most protein-rich cereal: {most_protein}")


@pipeline
def complex_pipeline():
    cereals = load_cereals()
    display_results(
        most_calories=sort_by_calories(cereals),
        most_protein=sort_by_protein(cereals),
    )


# end_complex_pipeline_marker_0

if __name__ == "__main__":
    result = execute_pipeline(complex_pipeline)
    assert result.success

# start_complex_pipeline_marker_1
def test_complex_pipeline():
    res = execute_pipeline(complex_pipeline)
    assert res.success
    assert len(res.solid_result_list) == 4
    for solid_res in res.solid_result_list:
        assert solid_res.success


# end_complex_pipeline_marker_1
