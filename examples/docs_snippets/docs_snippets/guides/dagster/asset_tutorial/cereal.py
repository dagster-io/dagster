"""isort:skip_file"""

# start_asset_marker
import csv
import requests
from dagster import asset


@asset
def cereals():
    response = requests.get("https://docs.dagster.io/assets/cereal.csv")
    lines = response.text.split("\n")
    cereal_rows = [row for row in csv.DictReader(lines)]

    return cereal_rows


# end_asset_marker

# start_materialize_marker
from dagster import materialize

if __name__ == "__main__":
    materialize([cereals])

# end_materialize_marker
