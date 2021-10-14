import csv

import requests
from dagster import solid


# start_download_cereals_marker
@solid
def download_cereals():
    response = requests.get("https://docs.dagster.io/assets/cereal.csv")
    lines = response.text.split("\n")
    return [row for row in csv.DictReader(lines)]


# end_download_cereals_marker


# start_download_csv_marker
@solid
def download_csv(context):
    response = requests.get(context.solid_config["url"])
    lines = response.text.split("\n")
    return [row for row in csv.DictReader(lines)]


# end_download_csv_marker
