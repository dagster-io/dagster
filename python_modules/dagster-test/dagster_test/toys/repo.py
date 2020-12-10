from dagster import repository
from dagster_test.toys.branches import branch_pipeline
from dagster_test.toys.composition import composition
from dagster_test.toys.dynamic import dynamic_pipeline
from dagster_test.toys.error_monster import error_monster
from dagster_test.toys.hammer import hammer_pipeline
from dagster_test.toys.log_file import log_file_pipeline
from dagster_test.toys.log_spew import log_spew
from dagster_test.toys.longitudinal import longitudinal_pipeline
from dagster_test.toys.many_events import many_events
from dagster_test.toys.retries import retry_pipeline
from dagster_test.toys.sleepy import sleepy_pipeline
from dagster_test.toys.unreliable import unreliable_pipeline

from .schedules import get_toys_schedules
from .sensors import get_toys_sensors


@repository
def toys_repository():
    return (
        [
            composition,
            error_monster,
            hammer_pipeline,
            log_file_pipeline,
            log_spew,
            longitudinal_pipeline,
            many_events,
            sleepy_pipeline,
            retry_pipeline,
            branch_pipeline,
            unreliable_pipeline,
            dynamic_pipeline,
        ]
        + get_toys_schedules()
        + get_toys_sensors()
    )
