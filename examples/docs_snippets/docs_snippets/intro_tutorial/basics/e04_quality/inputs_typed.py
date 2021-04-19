import csv

import requests
from dagster import execute_pipeline, pipeline, solid


# start_inputs_typed_marker_0
@solid
def download_csv(context, url: str):
    response = requests.get(url)
    lines = response.text.split("\n")
    context.log.info("Read {n_lines} lines".format(n_lines=len(lines)))
    return [row for row in csv.DictReader(lines)]


# end_inputs_typed_marker_0


@solid
def sort_by_calories(context, cereals):
    sorted_cereals = sorted(cereals, key=lambda cereal: cereal["calories"])
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
def inputs_pipeline():
    sort_by_calories(download_csv())


if __name__ == "__main__":
    result = execute_pipeline(
        inputs_pipeline,
        run_config={
            "solids": {
                "download_csv": {
                    "inputs": {
                        "url": {
                            "value": "https://raw.githubusercontent.com/dagster-io/dagster/master/examples/docs_snippets/docs_snippets/intro_tutorial/cereal.csv"
                        }
                    }
                }
            }
        },
    )
    assert result.success
