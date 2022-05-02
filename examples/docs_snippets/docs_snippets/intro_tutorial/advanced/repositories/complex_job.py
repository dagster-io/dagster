import csv
import os

from dagster import job, op


@op
def load_cereals():
    dataset_path = os.path.join(os.path.dirname(__file__), "cereal.csv")
    with open(dataset_path, "r", encoding="utf8") as fd:
        cereals = [row for row in csv.DictReader(fd)]
    return cereals


@op
def sort_by_calories(cereals):
    sorted_cereals = list(sorted(cereals, key=lambda cereal: cereal["calories"]))
    least_caloric = sorted_cereals[0]["name"]
    most_caloric = sorted_cereals[-1]["name"]
    return (least_caloric, most_caloric)


@op
def sort_by_protein(cereals):
    sorted_cereals = list(sorted(cereals, key=lambda cereal: cereal["protein"]))
    least_protein = sorted_cereals[0]["name"]
    most_protein = sorted_cereals[-1]["name"]
    return (least_protein, most_protein)


@op
def display_results(context, calorie_results, protein_results):
    context.log.info(f"Most caloric cereal: {calorie_results[-1]}")
    context.log.info(f"Most protein-rich cereal: {protein_results[-1]}")


@job
def complex_job():
    cereals = load_cereals()
    display_results(
        calorie_results=sort_by_calories(cereals),
        protein_results=sort_by_protein(cereals),
    )


if __name__ == "__main__":
    result = complex_job.execute_in_process()
    assert result.success


def test_complex_pipeline():
    res = complex_job.execute_in_process()
    assert res.success
    assert len(res.op_result_list) == 4
    for op_res in res.op_result_list:
        assert op_res.success
