# for NormalizedCereal.__table__.insert().execute(records)
# pylint: disable=no-member
import csv
import sqlite3
from copy import deepcopy
from typing import Any

import requests
import sqlalchemy
import sqlalchemy.ext.declarative
from dagster import (
    Field,
    String,
    config_from_files,
    file_relative_path,
    graph,
    op,
    repository,
    resource,
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


Base = sqlalchemy.ext.declarative.declarative_base()  # type: Any


class NormalizedCereal(Base):
    __tablename__ = "normalized_cereals"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    mfr = sqlalchemy.Column(sqlalchemy.String)
    type = sqlalchemy.Column(sqlalchemy.String)
    calories = sqlalchemy.Column(sqlalchemy.Float)
    protein = sqlalchemy.Column(sqlalchemy.Float)
    fat = sqlalchemy.Column(sqlalchemy.Float)
    sodium = sqlalchemy.Column(sqlalchemy.Float)
    fiber = sqlalchemy.Column(sqlalchemy.Float)
    carbo = sqlalchemy.Column(sqlalchemy.Float)
    sugars = sqlalchemy.Column(sqlalchemy.Float)
    potass = sqlalchemy.Column(sqlalchemy.Float)
    vitamins = sqlalchemy.Column(sqlalchemy.Float)
    shelf = sqlalchemy.Column(sqlalchemy.Float)
    weight = sqlalchemy.Column(sqlalchemy.Float)
    cups = sqlalchemy.Column(sqlalchemy.Float)
    rating = sqlalchemy.Column(sqlalchemy.Float)


class SqlAlchemyPostgresWarehouse:
    def __init__(self, conn_str):
        self._conn_str = conn_str
        self._engine = sqlalchemy.create_engine(self._conn_str)

    def update_normalized_cereals(self, records):
        Base.metadata.bind = self._engine
        Base.metadata.drop_all(self._engine)
        Base.metadata.create_all(self._engine)
        NormalizedCereal.__table__.insert().execute(records)


@resource(config_schema={"conn_str": Field(String)})
def sqlalchemy_postgres_warehouse_resource(context):
    return SqlAlchemyPostgresWarehouse(context.resource_config["conn_str"])


@op
def download_csv(context):
    response = requests.get("https://docs.dagster.io/assets/cereal.csv")
    lines = response.text.split("\n")
    context.log.info("Read {n_lines} lines".format(n_lines=len(lines)))
    return [row for row in csv.DictReader(lines)]


@op(required_resource_keys={"warehouse"})
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


# start_presets_marker_0
@graph
def calories():
    normalize_calories(download_csv())


calories_test_job = calories.to_job(
    resource_defs={"warehouse": local_sqlite_warehouse_resource},
    config={"resources": {"warehouse": {"config": {"conn_str": ":memory:"}}}},
)
calories_dev_job = calories.to_job(
    resource_defs={"warehouse": sqlalchemy_postgres_warehouse_resource},
    config=config_from_files(
        [file_relative_path(__file__, "presets_dev_warehouse.yaml")]
    ),
)


# end_presets_marker_0


if __name__ == "__main__":
    # start_presets_main
    result = calories_test_job.execute_in_process()
    # end_presets_main
    assert result.success


# start_repo_marker
@repository
def dev_repo():
    return [calories_dev_job]


# end_repo_marker
