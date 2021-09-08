import pendulum
from dagster import AssetMaterialization, Output, graph, op, repository
from dagster_test.graph_job_op_toys.log_s3 import log_s3_job
from dagster_test.graph_job_op_toys.error_monster import error_monster_failing_job

from .schedules import get_toys_schedules
from .sensors import get_toys_sensors


@op
def materialization_op():
    timestamp = pendulum.now("UTC").timestamp()
    yield AssetMaterialization(asset_key="model", metadata={"timestamp": timestamp})
    yield Output(1)


@graph
def model():
    materialization_op()


model_job = model.to_job()


@repository
def toys_repository():
    return (
        [
            error_monster_failing_job,
            log_s3_job,
        ]
        + get_toys_schedules()
        + get_toys_sensors()
    )
