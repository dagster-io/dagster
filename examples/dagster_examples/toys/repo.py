from dagster import RepositoryDefinition

from dagster_examples.toys.config_mapping import config_mapping_pipeline
from dagster_examples.toys.error_monster import error_monster
from dagster_examples.toys.sleepy import sleepy_pipeline
from dagster_examples.toys.log_demo import hello_logs_pipeline, hello_error_pipeline
from dagster_examples.toys.log_spew import define_spew_pipeline
from dagster_examples.toys.many_events import many_events
from dagster_examples.toys.composition import composition


def define_repo():
    return RepositoryDefinition(
        name='toys_repository',
        pipeline_dict={
            'sleepy': sleepy_pipeline,
            'error_monster': error_monster,
            'hello_error': hello_error_pipeline,
            'hello_logs': hello_logs_pipeline,
            'log_spew': define_spew_pipeline,
            'many_events': many_events,
            'composition': composition,
            'config_mapping': config_mapping_pipeline,
        },
    )
