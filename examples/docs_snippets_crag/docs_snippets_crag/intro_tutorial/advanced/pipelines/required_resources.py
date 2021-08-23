import csv
import sqlite3
from copy import deepcopy

import requests
from dagster import (
    Field,
    ModeDefinition,
    String,
    execute_pipeline,
    pipeline,
    resource,
    solid,
)


class LocalSQLiteWarehouse:
    def __init__(self, conn_str):
        self._conn_str = conn_str

    def update_normalized_cereals(self, records):
        conn = sqlite3.connect("example.db")
        curs = conn.cursor()
        try:
            curs.execute("DROP TABLE IF EXISTS normalized_cereals")
            curs.execute(
                """CREATE TABLE IF NOT EXISTS normalized_cereals
                (name text, mfr text, type text, calories real,
                 protein real, fat real, sodium real, fiber real,
                 carbo real, sugars real, potass real, vitamins real,
                 shelf real, weight real, cups real, rating real)"""
            )
            curs.executemany(
                """INSERT INTO normalized_cereals VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [tuple(record.values()) for record in records],
            )
        finally:
            curs.close()


@resource(config_schema={"conn_str": Field(String)})
def local_sqlite_warehouse_resource(context):
    return LocalSQLiteWarehouse(context.resource_config["conn_str"])


@solid
def download_csv(context):
    response = requests.get("https://docs.dagster.io/assets/cereal.csv")
    lines = response.text.split("\n")
    context.log.info("Read {n_lines} lines".format(n_lines=len(lines)))
    return [row for row in csv.DictReader(lines)]


# start_required_resources_marker_0
@solid(required_resource_keys={"warehouse"})
def normalize_calories(context, cereals):
    columns_to_normalize = [
        "calories",
        "protein",
        "fat",
        "sodium",
        "fiber",
        "carbo",
        "sugars",
        "potass",
        "vitamins",
        "weight",
    ]
    quantities = [cereal["cups"] for cereal in cereals]
    reweights = [1.0 / float(quantity) for quantity in quantities]

    normalized_cereals = deepcopy(cereals)
    for idx in range(len(normalized_cereals)):
        cereal = normalized_cereals[idx]
        for column in columns_to_normalize:
            cereal[column] = float(cereal[column]) * reweights[idx]

    context.resources.warehouse.update_normalized_cereals(normalized_cereals)


# end_required_resources_marker_0


@pipeline(
    mode_defs=[
        ModeDefinition(
            resource_defs={"warehouse": local_sqlite_warehouse_resource}
        )
    ]
)
def resources_pipeline():
    normalize_calories(download_csv())


if __name__ == "__main__":
    run_config = {
        "resources": {"warehouse": {"config": {"conn_str": ":memory:"}}}
    }
    result = execute_pipeline(resources_pipeline, run_config=run_config)
    assert result.success
