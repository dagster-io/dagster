import math
import time
from datetime import datetime
from random import random

from dagster import (
    AssetMaterialization,
    EventMetadataEntry,
    InputDefinition,
    ModeDefinition,
    Nothing,
    OutputDefinition,
    fs_io_manager,
    pipeline,
    solid,
)
from dagster.utils.partitions import DEFAULT_DATE_FORMAT

TRAFFIC_CONSTANTS = {
    0: 1,
    1: 0.92,
    2: 0.88,
    3: 0.86,
    4: 0.81,
    5: 0.69,
    6: 0.65,
}
SLEEP_INGEST = 0.001
SLEEP_PERSIST = 0.001
SLEEP_BUILD = 0.001 * 0.001
SLEEP_TRAIN = 0.001 * 0.001


INITIAL_DATE = datetime.strptime("2020-01-01", DEFAULT_DATE_FORMAT)


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


def growth_rate(partition_date):
    weeks_since_init = (partition_date - INITIAL_DATE).days / 7
    return sigmoid(weeks_since_init - 4)  # make some sort of S-curve


def traffic_data_size(partition_date):
    return TRAFFIC_CONSTANTS[partition_date.weekday()] * 10000 * growth_rate(partition_date)


def cost_data_size(partition_date):
    return 3000 + 1000 * math.log(10000 * growth_rate(partition_date), 10)


def combined_data_size(partition_date):
    return traffic_data_size(partition_date) * cost_data_size(partition_date)


def make_solid(
    name,
    asset_key=None,
    error_rate=None,
    data_size_fn=None,
    materialization_metadata_entries=None,
    sleep_factor=None,
    has_input=False,
):
    @solid(
        name=name,
        config_schema={"partition": str},
        input_defs=[InputDefinition("the_input", dagster_type=Nothing)] if has_input else [],
        output_defs=[OutputDefinition(Nothing)],
    )
    def made_solid(context):
        partition_date = datetime.strptime(context.solid_config["partition"], DEFAULT_DATE_FORMAT)
        if data_size_fn:
            data_size = data_size_fn(partition_date)
            sleep_time = sleep_factor * data_size

            time.sleep(sleep_time)

        if error_rate and random() < error_rate:
            raise Exception("blah")

        if asset_key:
            metadata_entries = materialization_metadata_entries or []
            if data_size_fn:
                metadata_entries.append(EventMetadataEntry.float(data_size, "Data size (bytes)"))

            if len(metadata_entries) == 0:
                metadata_entries = None

            yield AssetMaterialization(
                asset_key=asset_key,
                metadata_entries=metadata_entries,
                partition=context.solid_config.get("partition"),
            )

    return made_solid


@pipeline(
    description=(
        "Demo pipeline that simulates growth of execution-time and data-throughput of a data pipeline "
        "following a sigmoidal curve"
    ),
    mode_defs=[ModeDefinition(resource_defs={"io_manager": fs_io_manager})],
)
def longitudinal_pipeline():
    ingest_costs = make_solid(
        "ingest_costs", error_rate=0.15, sleep_factor=SLEEP_INGEST, data_size_fn=cost_data_size
    )
    persist_costs = make_solid(
        "persist_costs",
        asset_key="cost_db_table",
        has_input=True,
        error_rate=0.01,
        sleep_factor=SLEEP_PERSIST,
        data_size_fn=cost_data_size,
    )
    ingest_traffic = make_solid(
        "ingest_traffic", error_rate=0.1, sleep_factor=SLEEP_INGEST, data_size_fn=traffic_data_size
    )
    persist_traffic = make_solid(
        "persist_traffic",
        asset_key="traffic_db_table",
        has_input=True,
        sleep_factor=SLEEP_PERSIST,
        data_size_fn=traffic_data_size,
        error_rate=0.01,
    )
    build_model = make_solid(
        "build_model", has_input=True, sleep_factor=SLEEP_BUILD, data_size_fn=combined_data_size
    )
    train_model = make_solid(
        "train_model", has_input=True, sleep_factor=SLEEP_TRAIN, data_size_fn=combined_data_size
    )
    persist_model = make_solid("persist_model", asset_key="traffic_cost_model", has_input=True)
    build_cost_dashboard = make_solid(
        "build_cost_dashboard",
        asset_key=["dashboards", "cost_dashboard"],
        has_input=True,
        materialization_metadata_entries=[
            EventMetadataEntry.url("http://docs.dagster.io/cost", "Documentation URL")
        ],
    )
    build_traffic_dashboard = make_solid(
        "build_traffic_dashboard",
        asset_key=["dashboards", "traffic_dashboard"],
        has_input=True,
        materialization_metadata_entries=[
            EventMetadataEntry.url("http://docs.dagster.io/traffic", "Documentation URL")
        ],
    )

    cost_data = persist_costs(ingest_costs())
    traffic_data = persist_traffic(ingest_traffic())
    persist_model(train_model(build_model([cost_data, traffic_data])))

    build_cost_dashboard(cost_data)
    build_traffic_dashboard(traffic_data)
