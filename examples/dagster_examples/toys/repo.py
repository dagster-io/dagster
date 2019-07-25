from dagster import RepositoryDefinition

from dagster_examples.toys.config_mapping import config_mapping_pipeline
from dagster_examples.toys.error_monster import error_monster
from dagster_examples.toys.sleepy import sleepy_pipeline
from dagster_examples.toys.log_demo import hello_logs_pipeline, hello_error_pipeline
from dagster_examples.toys.log_spew import log_spew
from dagster_examples.toys.many_events import many_events
from dagster_examples.toys.composition import composition
from dagster_examples.toys.resources_error import resource_error_pipeline


def define_repo():
    return RepositoryDefinition(
        name='toys_repository',
        pipeline_defs=[
            sleepy_pipeline,
            error_monster,
            hello_error_pipeline,
            hello_logs_pipeline,
            log_spew,
            many_events,
            composition,
            config_mapping_pipeline,
            resource_error_pipeline,
        ],
    )
