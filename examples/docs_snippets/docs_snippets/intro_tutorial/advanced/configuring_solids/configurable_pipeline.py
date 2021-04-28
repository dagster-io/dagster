# start_pipeline_marker
import csv

import requests
from dagster import execute_pipeline, pipeline, solid


@solid
def download_csv(context):
    response = requests.get(context.solid_config["url"])
    lines = response.text.split("\n")
    return [row for row in csv.DictReader(lines)]


@solid
def sort_by_calories(context, cereals):
    sorted_cereals = sorted(
        cereals, key=lambda cereal: int(cereal["calories"])
    )

    context.log.info(f'Most caloric cereal: {sorted_cereals[-1]["name"]}')


@pipeline
def configurable_pipeline():
    sort_by_calories(download_csv())


# end_pipeline_marker

if __name__ == "__main__":
    # start_run_config_marker
    run_config = {
        "solids": {
            "download_csv": {
                "config": {"url": "https://docs.dagster.io/assets/cereal.csv"}
            }
        }
    }
    # end_run_config_marker
    # start_execute_marker
    result = execute_pipeline(configurable_pipeline, run_config=run_config)
    # end_execute_marker
    assert result.success
