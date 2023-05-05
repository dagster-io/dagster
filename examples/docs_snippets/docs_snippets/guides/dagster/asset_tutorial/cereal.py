# isort: skip_file

import csv
import requests
from dagster import asset


# start_asset_marker
import csv
import requests
from dagster import asset


@asset
def cereals():  # type: ignore  # (didactic)
    response = requests.get("https://docs.dagster.io/assets/cereal.csv")
    lines = response.text.split("\n")
    cereal_rows = [row for row in csv.DictReader(lines)]

    return cereal_rows


# end_asset_marker

# start_multiple_assets
import csv
import requests
from dagster import asset


@asset
def cereals():
    response = requests.get("https://docs.dagster.io/assets/cereal.csv")
    lines = response.text.split("\n")
    return [row for row in csv.DictReader(lines)]


@asset
def nabisco_cereals(cereals):
    """Cereals manufactured by Nabisco."""
    return [row for row in cereals if row["mfr"] == "N"]


# end_multiple_assets

# start_materialize_marker
from dagster import materialize

if __name__ == "__main__":
    materialize([cereals])

# end_materialize_marker


# start_multiple_materialize_marker
from dagster import materialize

if __name__ == "__main__":
    materialize([cereals, nabisco_cereals])

# end_multiple_materialize_marker
