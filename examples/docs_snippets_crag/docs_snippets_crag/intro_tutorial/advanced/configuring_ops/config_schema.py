import csv

import requests
from dagster import op


@op(config_schema={"url": str})
def download_csv(context):
    response = requests.get(context.op_config["url"])
    lines = response.text.split("\n")
    return [row for row in csv.DictReader(lines)]
