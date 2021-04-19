import csv

import requests
from dagster import solid


# start_download_cereals_marker
@solid
def download_cereals(_):
    response = requests.get(
        "https://raw.githubusercontent.com/dagster-io/dagster/master/examples/docs_snippets/docs_snippets/intro_tutorial/cereal.csv"
    )
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
