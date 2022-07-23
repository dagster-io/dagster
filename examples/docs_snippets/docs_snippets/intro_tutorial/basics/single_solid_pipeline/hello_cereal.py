# isort: skip_file

# start_solid_marker
import requests
import csv
from dagster import job, op, get_dagster_logger


@op
def hello_cereal():
    response = requests.get("https://docs.dagster.io/assets/cereal.csv")
    lines = response.text.split("\n")
    cereals = [row for row in csv.DictReader(lines)]
    get_dagster_logger().info(f"Found {len(cereals)} cereals")


# end_solid_marker


# start_pipeline_marker
@job
def hello_cereal_job():
    hello_cereal()


# end_pipeline_marker

# start_execute_marker
if __name__ == "__main__":
    result = hello_cereal_job.execute_in_process()

# end_execute_marker
