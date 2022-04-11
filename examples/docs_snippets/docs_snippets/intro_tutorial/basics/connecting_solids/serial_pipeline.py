import csv

import requests

from dagster import get_dagster_logger, job, op


@op
def download_cereals():
    response = requests.get("https://docs.dagster.io/assets/cereal.csv")
    lines = response.text.split("\n")
    return [row for row in csv.DictReader(lines)]


@op
def find_sugariest(cereals):
    sorted_by_sugar = sorted(cereals, key=lambda cereal: cereal["sugars"])
    get_dagster_logger().info(f'{sorted_by_sugar[-1]["name"]} is the sugariest cereal')


@job
def serial():
    find_sugariest(download_cereals())
