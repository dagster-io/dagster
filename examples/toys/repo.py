from dagster import RepositoryDefinition

from error_monster import define_pipeline
from sleepy import define_sleepy_pipeline
from log_spew import define_spew_pipeline


def define_repo():
    return RepositoryDefinition(
        name='toys_repository',
        pipeline_dict={
            'sleepy': define_sleepy_pipeline,
            'error_monster': define_pipeline,
            'log_spew': define_spew_pipeline,
        },
    )
