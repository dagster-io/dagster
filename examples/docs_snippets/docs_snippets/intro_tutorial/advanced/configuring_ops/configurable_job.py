# start_job_marker
import csv

import requests
from dagster import get_dagster_logger, job, op


@op
def download_csv(context):
    response = requests.get(context.op_config["url"])
    lines = response.text.split("\n")
    return [row for row in csv.DictReader(lines)]


@op
def sort_by_calories(cereals):
    sorted_cereals = sorted(
        cereals, key=lambda cereal: int(cereal["calories"])
    )

    get_dagster_logger().info(
        f'Most caloric cereal: {sorted_cereals[-1]["name"]}'
    )


@job
def configurable_job():
    sort_by_calories(download_csv())


# end_job_marker

if __name__ == "__main__":
    # start_run_config_marker
    run_config = {
        "ops": {
            "download_csv": {
                "config": {"url": "https://docs.dagster.io/assets/cereal.csv"}
            }
        }
    }
    # end_run_config_marker
    # start_execute_marker
    result = configurable_job.execute_in_process(run_config=run_config)
    # end_execute_marker
    assert result.success
