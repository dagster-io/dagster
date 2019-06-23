from dagster import RepositoryDefinition

from dagster_examples.toys.config_mapping import config_mapping_pipeline
from dagster_examples.toys.error_monster import define_error_monster_pipeline
from dagster_examples.toys.sleepy import define_sleepy_pipeline
from dagster_examples.toys.log_demo import define_hello_logs_pipeline, define_hello_error_pipeline
from dagster_examples.toys.log_spew import define_spew_pipeline
from dagster_examples.toys.many_events import define_many_events_pipeline
from dagster_examples.toys.composition import define_composition_pipeline


def define_repo():
    return RepositoryDefinition(
        name='toys_repository',
        pipeline_dict={
            'sleepy': define_sleepy_pipeline,
            'error_monster': define_error_monster_pipeline,
            'hello_error': define_hello_error_pipeline,
            'hello_logs': define_hello_logs_pipeline,
            'log_spew': define_spew_pipeline,
            'many_events': define_many_events_pipeline,
            'composition': define_composition_pipeline,
            'config_mapping': config_mapping_pipeline,
        },
    )
