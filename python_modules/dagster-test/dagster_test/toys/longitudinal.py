import math
import time
from datetime import datetime
from random import random

from dagster import (
    Array,
    AssetKey,
    AssetMaterialization,
    EventMetadataEntry,
    Field,
    Output,
    Permissive,
    pipeline,
    solid,
)
from dagster.utils.partitions import DEFAULT_DATE_FORMAT


def _base_config():
    return {
        "error_rate": Field(float, is_required=False, default_value=0.0),
        "sleep": Field(float, is_required=False, default_value=0.5),
        "materialization_key_list": Field(Array(str), is_required=False),
        "materialization_key": Field(str, is_required=False),
        "materialization_text": Field(str, is_required=False),
        "materialization_url": Field(str, is_required=False),
        "materialization_path": Field(str, is_required=False),
        "materialization_json": Field(Permissive(), is_required=False),
        "materialization_value": Field(float, is_required=False),
        "partition": Field(str, is_required=False),
    }


def _base_compute(context):
    time.sleep(context.solid_config["sleep"])

    if random() < context.solid_config["error_rate"]:
        raise Exception("blah")

    asset_key = None
    if context.solid_config.get("materialization_key_list") is not None:
        asset_key = AssetKey(context.solid_config.get("materialization_key_list"))
    elif context.solid_config.get("materialization_key") is not None:
        asset_key = AssetKey(context.solid_config.get("materialization_key"))

    if asset_key:
        metadata_entries = []
        if context.solid_config.get("materialization_text") is not None:
            metadata_entries.append(
                EventMetadataEntry.text(
                    context.solid_config.get("materialization_text"),
                    context.solid.name,
                )
            )

        if context.solid_config.get("materialization_url") is not None:
            metadata_entries.append(
                EventMetadataEntry.url(
                    context.solid_config.get("materialization_url"),
                    context.solid.name,
                )
            )

        if context.solid_config.get("materialization_path") is not None:
            metadata_entries.append(
                EventMetadataEntry.path(
                    context.solid_config.get("materialization_path"),
                    context.solid.name,
                )
            )

        if context.solid_config.get("materialization_json") is not None:
            metadata_entries.append(
                EventMetadataEntry.json(
                    context.solid_config.get("materialization_json"),
                    context.solid.name,
                )
            )

        if context.solid_config.get("materialization_value") is not None:
            metadata_entries = [
                EventMetadataEntry.float(
                    context.solid_config.get("materialization_value"),
                    context.solid.name,
                )
            ]

        if len(metadata_entries) == 0:
            metadata_entries = None

        yield AssetMaterialization(
            asset_key=asset_key,
            metadata_entries=metadata_entries,
            partition=context.solid_config.get("partition"),
        )

    yield Output(1)


@solid(config_schema=_base_config())
def base_no_input(context):
    for event in _base_compute(context):
        yield event


@solid(config_schema=_base_config())
def base_one_input(context, _):
    for event in _base_compute(context):
        yield event


@solid(config_schema=_base_config())
def base_two_inputs(context, _a, _b):
    for event in _base_compute(context):
        yield event


@pipeline(
    description=(
        "Demo pipeline that simulates growth of execution-time and data-throughput of a data pipeline "
        "following a sigmoidal curve"
    )
)
def longitudinal_pipeline():
    ingest_costs = base_no_input.alias("ingest_costs")
    persist_costs = base_one_input.alias("persist_costs")
    ingest_traffic = base_no_input.alias("ingest_traffic")
    persist_traffic = base_one_input.alias("persist_traffic")
    build_model = base_two_inputs.alias("build_model")
    train_model = base_one_input.alias("train_model")
    persist_model = base_one_input.alias("persist_model")
    build_cost_dashboard = base_one_input.alias("build_cost_dashboard")
    build_traffic_dashboard = base_one_input.alias("build_traffic_dashboard")

    cost_data = persist_costs(ingest_costs())
    traffic_data = persist_traffic(ingest_traffic())
    persist_model(train_model(build_model(cost_data, traffic_data)))

    build_cost_dashboard(cost_data)
    build_traffic_dashboard(traffic_data)


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


def longitudinal_config(partition):
    partition_date = datetime.strptime(partition.name, DEFAULT_DATE_FORMAT)
    weeks_since_init = (partition_date - INITIAL_DATE).days / 7
    growth_rate = sigmoid(weeks_since_init - 4)  # make some sort of S-curve
    cost_data_size = 3000 + 1000 * math.log(10000 * growth_rate, 10)
    traffic_data_size = TRAFFIC_CONSTANTS[partition_date.weekday()] * 10000 * growth_rate

    return {
        "intermediate_storage": {"filesystem": {}},
        "solids": {
            "ingest_costs": {
                "config": {
                    "error_rate": random() * 0.15,  # ingestion is slightly error prone
                    "sleep": SLEEP_INGEST * cost_data_size,  # sleep dependent on data size
                    "partition": partition.name,
                }
            },
            "persist_costs": {
                "config": {
                    "error_rate": random() * 0.01,  # ingestion is slightly error prone
                    "sleep": SLEEP_PERSIST * cost_data_size,  # sleep dependent on data size
                    "materialization_key": "cost_db_table",
                    "materialization_value": cost_data_size,
                    "partition": partition.name,
                }
            },
            "ingest_traffic": {
                "config": {
                    "error_rate": random() * 0.15,  # ingestion is slightly error prone
                    "sleep": SLEEP_INGEST * traffic_data_size,  # sleep dependent on data size
                    "partition": partition.name,
                }
            },
            "persist_traffic": {
                "config": {
                    "error_rate": random() * 0.01,  # ingestion is slightly error prone
                    "sleep": SLEEP_PERSIST * traffic_data_size,
                    "materialization_key": "traffic_db_table",
                    "materialization_value": traffic_data_size,
                    "partition": partition.name,
                }
            },
            "build_cost_dashboard": {
                "config": {
                    "materialization_key_list": ["dashboards", "cost_dashboard"],
                    "materialization_url": "http://docs.dagster.io/cost",
                    "partition": partition.name,
                }
            },
            "build_traffic_dashboard": {
                "config": {
                    "materialization_key_list": ["dashboards", "traffic_dashboard"],
                    "materialization_url": "http://docs.dagster.io/traffic",
                    "partition": partition.name,
                }
            },
            "build_model": {
                "config": {
                    "sleep": SLEEP_BUILD
                    * traffic_data_size
                    * cost_data_size,  # sleep dependent on data size
                    "partition": partition.name,
                }
            },
            "train_model": {
                "config": {
                    "sleep": SLEEP_TRAIN
                    * traffic_data_size
                    * cost_data_size,  # sleep dependent on data size
                    "partition": partition.name,
                }
            },
            "persist_model": {
                "config": {
                    "materialization_key": "model",
                    "materialization_json": {
                        "traffic": traffic_data_size,
                        "cost": cost_data_size,
                    },
                    "partition": partition.name,
                }
            },
        },
    }
