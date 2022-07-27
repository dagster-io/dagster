import math
import time
from datetime import datetime
from random import random

from dagster import (
    AssetMaterialization,
    InputDefinition,
    ModeDefinition,
    Nothing,
    OutputDefinition,
    fs_io_manager,
)
from dagster._legacy import pipeline, solid
from dagster._utils.partitions import DEFAULT_DATE_FORMAT

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


def users_data_size(partition_date):
    return TRAFFIC_CONSTANTS[partition_date.weekday()] * 10000 * growth_rate(partition_date)


def video_views_data_size(partition_date):
    return 3000 + 1000 * math.log(10000 * growth_rate(partition_date), 10)


def combined_data_size(partition_date):
    return users_data_size(partition_date) * video_views_data_size(partition_date)


class IntentionalRandomFailure(Exception):
    """To distinguish from other errors"""


def make_solid(
    name,
    asset_key=None,
    error_rate=None,
    data_size_fn=None,
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

        rand = random()
        if error_rate and rand < error_rate:
            raise IntentionalRandomFailure(f"random {rand} < error rate {error_rate}")

        if asset_key:
            metadata = {"Data size (bytes)": data_size} if data_size_fn else None

            yield AssetMaterialization(
                asset_key=asset_key,
                metadata=metadata,
                partition=context.solid_config.get("partition"),
            )

    return made_solid


@pipeline(
    description=(
        "Demo pipeline that simulates updating tables of users and video views and training a "
        "video recommendation model. The growth of execution-time and data-throughput follows"
        "a sigmoidal curve."
    ),
    mode_defs=[ModeDefinition(resource_defs={"io_manager": fs_io_manager})],
)
def longitudinal_pipeline():
    ingest_raw_video_views = make_solid(
        "ingest_raw_video_views",
        asset_key="raw_video_views",
        error_rate=0.15,
        sleep_factor=SLEEP_INGEST,
        data_size_fn=video_views_data_size,
    )
    update_video_views_table = make_solid(
        "update_video_views_table",
        asset_key="video_views",
        has_input=True,
        error_rate=0.01,
        sleep_factor=SLEEP_PERSIST,
        data_size_fn=video_views_data_size,
    )
    ingest_raw_users = make_solid(
        "ingest_raw_users",
        "raw_users",
        error_rate=0.1,
        sleep_factor=SLEEP_INGEST,
        data_size_fn=users_data_size,
    )
    update_users_table = make_solid(
        "update_users_table",
        asset_key="users",
        has_input=True,
        sleep_factor=SLEEP_PERSIST,
        data_size_fn=users_data_size,
        error_rate=0.01,
    )
    train_video_recommender_model = make_solid(
        "train_video_recommender_model",
        has_input=True,
        sleep_factor=SLEEP_TRAIN,
        data_size_fn=combined_data_size,
    )

    video_views = update_video_views_table(ingest_raw_video_views())
    users = update_users_table(ingest_raw_users())
    train_video_recommender_model([video_views, users])
