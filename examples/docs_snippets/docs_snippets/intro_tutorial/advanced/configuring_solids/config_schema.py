import csv
import os

from dagster import solid


# start_read_csv_marker
@solid(config_schema={"csv_name": str})
def read_csv(context):
    csv_path = os.path.join(
        os.path.dirname(__file__), context.solid_config["csv_name"]
    )
    with open(csv_path, "r") as fd:
        lines = [row for row in csv.DictReader(fd)]

    context.log.info(f"Read {len(lines)} lines")
    return lines


# end_read_csv_marker
