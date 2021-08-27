import csv

import requests
from dagster import ModeDefinition, fs_io_manager, pipeline, solid


@solid
def download_cereals():
    response = requests.get("https://docs.dagster.io/assets/cereal.csv")
    lines = response.text.split("\n")
    return [row for row in csv.DictReader(lines)]


@solid
def find_sugariest(context, cereals):
    sorted_by_sugar = sorted(cereals, key=lambda cereal: cereal["sugars"])
    context.log.info(f'{sorted_by_sugar[-1]["name"]} is the sugariest cereal')


@pipeline(mode_defs=[ModeDefinition(resource_defs={"io_manager": fs_io_manager})])
def hello_cereal_pipeline():
    find_sugariest(download_cereals())
