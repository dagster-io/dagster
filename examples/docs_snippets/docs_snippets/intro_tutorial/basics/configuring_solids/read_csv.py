import csv
import pathlib

from dagster import solid


# start_load_cereals_marker
@solid
def load_cereals(context):
    csv_path = pathlib.Path(__file__).parent / "cereal.csv"
    with open(csv_path, "r") as fd:
        cereals = [row for row in csv.DictReader(fd)]

    context.log.info(f"Found {len(cereals)} cereals")
    return cereals


# end_load_cereals_marker


# start_read_csv_marker
@solid(config_schema={"csv_name": str})
def read_csv(context):
    csv_path = pathlib.Path(__file__).parent / context.solid_config["csv_name"]
    with open(csv_path, "r") as fd:
        lines = [row for row in csv.DictReader(fd)]

    context.log.info(f"Read {len(lines)} lines")
    return lines


# end_read_csv_marker
