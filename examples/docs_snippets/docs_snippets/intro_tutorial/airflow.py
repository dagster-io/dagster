import csv

import requests

from dagster import OpExecutionContext, job, op


@op
def hello_cereal(context: OpExecutionContext):
    response = requests.get("https://docs.dagster.io/assets/cereal.csv")
    lines = response.text.split("\n")
    cereals = [row for row in csv.DictReader(lines)]
    context.log.info(f"Found {len(cereals)} cereals")

    return cereals


@job
def hello_cereal_pipeline():
    hello_cereal()
