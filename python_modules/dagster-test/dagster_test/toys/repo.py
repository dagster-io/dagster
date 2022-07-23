import pendulum
from dagster_test.toys.asset_lineage import asset_lineage_partition_set, asset_lineage_pipeline
from dagster_test.toys.branches import branch_pipeline
from dagster_test.toys.composition import composition
from dagster_test.toys.dynamic import dynamic_pipeline
from dagster_test.toys.error_monster import error_monster
from dagster_test.toys.hammer import hammer_pipeline
from dagster_test.toys.log_asset import log_asset_pipeline
from dagster_test.toys.log_file import log_file_pipeline
from dagster_test.toys.log_s3 import log_s3_pipeline
from dagster_test.toys.log_spew import log_spew
from dagster_test.toys.longitudinal import longitudinal_pipeline
from dagster_test.toys.many_events import many_events
from dagster_test.toys.notebooks import hello_world_notebook_pipeline
from dagster_test.toys.retries import retry_pipeline
from dagster_test.toys.sleepy import sleepy_pipeline
from dagster_test.toys.unreliable import unreliable_pipeline

from dagster import AssetMaterialization, Output, repository
from dagster._legacy import pipeline, solid

from .schedules import get_toys_schedules
from .sensors import get_toys_sensors


@solid
def materialization_solid(_):
    timestamp = pendulum.now("UTC").timestamp()
    yield AssetMaterialization(asset_key="model", metadata={"timestamp": timestamp})
    yield Output(1)


@pipeline
def model_pipeline():
    materialization_solid()


@repository
def toys_repository():
    return (
        [
            composition,
            error_monster,
            hammer_pipeline,
            log_asset_pipeline,
            log_file_pipeline,
            log_s3_pipeline,
            log_spew,
            longitudinal_pipeline,
            many_events,
            sleepy_pipeline,
            retry_pipeline,
            branch_pipeline,
            unreliable_pipeline,
            dynamic_pipeline,
            asset_lineage_pipeline,
            asset_lineage_partition_set,
            model_pipeline,
            hello_world_notebook_pipeline,
        ]
        + get_toys_schedules()
        + get_toys_sensors()
    )
